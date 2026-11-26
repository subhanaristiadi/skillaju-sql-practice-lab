"""Initialize an EMPTY Skillaju database. Credentials arrive on hidden stdin only.

Run: python scripts/seed_neon.py
Provide a JSON object with database_url when prompted. No secrets are logged.
Existing tables are never dropped, truncated or overwritten.
"""
import csv
import getpass
import io
import json
import sys
from pathlib import Path

import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[1]
TABLES = ('students','instructors','courses','enrollments','quiz_results')

def main():
    print('Ready for database configuration JSON on stdin (input is hidden).',flush=True)
    config=json.loads(getpass.getpass('Configuration: ') if sys.stdin.isatty() else sys.stdin.readline())
    connection=psycopg2.connect(config['database_url'],connect_timeout=15,sslmode='require')
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename=ANY(%s)",(list(TABLES),))
                if cursor.fetchall():
                    raise RuntimeError('Database already contains dataset tables; refusing to overwrite.')
                cursor.execute((ROOT/'skillaju_sql_project/schema.sql').read_text(encoding='utf-8'))
                counts={}
                for table in TABLES:
                    with (ROOT/f'{table}.csv').open(encoding='utf-8-sig',newline='') as source:
                        reader=csv.reader(source)
                        columns=next(reader)
                        output=io.StringIO()
                        writer=csv.writer(output)
                        count=0
                        for row in reader:
                            writer.writerow(row)
                            count+=1
                        output.seek(0)
                        statement=sql.SQL('COPY {} ({}) FROM STDIN WITH (FORMAT CSV, NULL \'\')').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,columns)))
                        cursor.copy_expert(statement.as_string(connection),output)
                        counts[table]=count
                # Database is new and isolated. Reader is granted explicitly after seeding.
                cursor.execute('REVOKE CREATE ON SCHEMA public FROM PUBLIC')
                cursor.execute('ANALYZE')
        print(json.dumps({'seeded':counts}),flush=True)
    finally:
        connection.close()

if __name__=='__main__':
    try: main()
    except Exception as error:
        # Connection exceptions can contain credentials, so print only the class.
        print(f'Seed failed: {type(error).__name__}',file=sys.stderr)
        sys.exit(1)
