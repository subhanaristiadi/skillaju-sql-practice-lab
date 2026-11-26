const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

const context = {window: {}, AbortSignal, setTimeout};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../api-client.js'), 'utf8'), context);
const createClient = context.window.SkillajuApi.createClient;
const response = (status, data) => ({status, ok: status >= 200 && status < 300, json: async () => data});

test('cold-start failures recover automatically without a GET preflight', async () => {
  const requests = [], delays = [];
  const client = createClient('https://sql.example', {
    fetch: async (url, options) => {
      requests.push({url, options});
      if (requests.length === 1) throw new TypeError('Failed to fetch');
      if (requests.length === 2) return response(503, {});
      return response(200, {status: 'ok'});
    },
    pause: async ms => delays.push(ms)
  });
  assert.equal((await client.request('/ready')).status, 'ok');
  assert.equal(requests.length, 3);
  assert.deepEqual(delays, [1000, 2000]);
  assert.equal(Object.keys(requests[0].options.headers).length, 0);
  assert.ok(requests.every(r => r.options.signal === requests[0].options.signal));
});

test('retry preserves read-only query payload', async () => {
  const bodies = [];
  const client = createClient('', {
    fetch: async (_, options) => {
      bodies.push(options.body);
      assert.equal(options.headers['Content-Type'], 'application/json');
      return response(bodies.length === 1 ? 502 : 200, {rows: [[1]]});
    }, pause: async () => {}
  });
  const body = JSON.stringify({sql: 'SELECT 1'});
  assert.equal((await client.request('/api/query', {method: 'POST', body})).rows[0][0], 1);
  assert.deepEqual(bodies, [body, body]);
});

test('SQL errors and rate limits are visible and are not retried', async () => {
  for (const status of [422, 429, 408]) {
    let calls = 0;
    const client = createClient('', {
      fetch: async () => {calls++; return response(status, {error: 'Query rejected', detail: 'Check SQL'});},
      pause: async () => assert.fail('Should not retry')
    });
    await assert.rejects(client.request('/api/query'), /Query rejected: Check SQL/);
    assert.equal(calls, 1);
  }
});

test('network retries stop after three attempts', async () => {
  let calls = 0;
  const client = createClient('', {
    fetch: async () => {calls++; throw new TypeError('Network unavailable');}, pause: async () => {}
  });
  await assert.rejects(client.request('/ready'), /Could not connect to the SQL service/);
  assert.equal(calls, 3);
});

test('the timeout applies to the whole request, including retries', async () => {
  const controller = new AbortController();
  let calls = 0;
  const client = createClient('', {
    fetch: async () => {calls++; controller.abort(); throw new DOMException('Aborted', 'AbortError');},
    pause: async () => assert.fail('Should not retry after timeout')
  });
  await assert.rejects(client.request('/ready', {signal: controller.signal}), /connection timed out/);
  assert.equal(calls, 1);
});
