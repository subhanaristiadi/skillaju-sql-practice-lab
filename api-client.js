// Connection retries are bounded to one 90-second window. SQL execution and
// validation are read-only, so transient network retries are safe here.
(function () {
  function createClient(base, options = {}) {
    const fetchRequest = options.fetch || ((...args) => fetch(...args));
    const pause = options.pause || (ms => new Promise(resolve => setTimeout(resolve, ms)));
    const timeoutMs = options.timeoutMs || 90000;

    async function request(path, opts = {}) {
      const signal = opts.signal || AbortSignal.timeout(timeoutMs);
      // GET requests must remain simple CORS requests. Sending Content-Type:
      // application/json on health/warmup GETs unnecessarily triggers preflight.
      const headers = opts.body
        ? { 'Content-Type': 'application/json', ...(opts.headers || {}) }
        : { ...(opts.headers || {}) };

      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          const response = await fetchRequest(base + path, { ...opts, headers, signal });
          if ([502, 503, 504].includes(response.status)) {
            throw Object.assign(new Error('The SQL service is still starting.'), { retryable: true });
          }
          let data;
          try { data = await response.json(); }
          catch {
            throw Object.assign(new Error('The SQL service did not return a valid response.'), { retryable: true });
          }
          if (!response.ok) {
            throw new Error([data.error || data.message || `HTTP ${response.status}`, data.detail].filter(Boolean).join(': '));
          }
          return data;
        } catch (error) {
          if (signal.aborted || ['AbortError', 'TimeoutError'].includes(error.name)) {
            throw new Error('The SQL connection timed out. Please run your query again.');
          }
          if (!(error.retryable || error.name === 'TypeError')) throw error;
          if (attempt === 2) {
            throw new Error('Could not connect to the SQL service. Check your internet connection and run the query again.');
          }
          await pause((attempt + 1) * 1000);
        }
      }
    }

    return { request };
  }

  window.SkillajuApi = { createClient };
})();
