"""Run every reference against Neon using hidden stdin credentials."""
import getpass
import json
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    print('Ready for verification configuration JSON on stdin (input is hidden).',flush=True)
    config=json.loads(getpass.getpass('Configuration: ') if sys.stdin.isatty() else sys.stdin.readline())
    os.environ['DATABASE_URL']=config['database_url']
    import server
    conn=server.connect_db()  # Also verifies role privileges and SELECT on all tables.
    failures=[]; rows={}
    with conn.cursor() as cur:
        cur.execute("SELECT current_user,current_setting('transaction_read_only')")
        print('Reader:',cur.fetchone(),flush=True)
        cur.execute("SELECT has_table_privilege(current_user,'public.students','SELECT'),has_table_privilege(current_user,'public.instructors','SELECT')")
        assert cur.fetchone()==(False,False),'Reader can access private identities'
        cur.execute("SELECT COUNT(*) FROM lab.students WHERE email NOT LIKE '%@example.invalid' OR name NOT LIKE 'Learner %'")
        assert cur.fetchone()[0]==0,'Practice identities are not anonymous'
        conn.rollback()
        for eid,ref in server.REFERENCES.items():
            try:
                sql=server.validate_sql(ref['sql'])
                cur.execute('SET LOCAL search_path TO lab, pg_catalog')
                cur.execute("SET LOCAL statement_timeout='10s'")
                cur.execute(sql)
                columns=[d.name for d in cur.description]
                result=cur.fetchmany(server.MAX_ROWS+1)
                expected=server.EXERCISES[eid]['expected_output']
                assert columns==expected,(columns,expected)
                assert len(result)<=server.MAX_ROWS,'Reference exceeds validation row limit'
                rows[eid]=len(result)
            except Exception as error:
                failures.append({'exercise':eid,'error':str(error)[:300]})
            finally: conn.rollback()
        cur.execute('SELECT (SELECT COUNT(*) FROM students),(SELECT COUNT(*) FROM courses),(SELECT COUNT(*) FROM instructors),(SELECT COUNT(*) FROM enrollments),(SELECT COUNT(*) FROM quiz_results)')
        assert cur.fetchone()==(3000,50,30,10380,30875)
        cur.execute('SELECT COUNT(*) FROM quiz_results q JOIN enrollments e USING(enrollment_id) WHERE q.student_id<>e.student_id OR q.course_id<>e.course_id')
        assert cur.fetchone()[0]==0
        conn.rollback()
    conn.close()
    report={'passed':len(rows),'failed':failures,'row_counts':rows}
    (ROOT/'.local').mkdir(exist_ok=True)
    (ROOT/'.local/reference-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report),flush=True)
    if failures: sys.exit(1)

if __name__=='__main__':
    try: main()
    except Exception as error:
        print(f'Verification failed: {type(error).__name__}',file=sys.stderr)
        sys.exit(1)
