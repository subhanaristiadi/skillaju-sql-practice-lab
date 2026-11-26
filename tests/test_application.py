import json
import re
import unittest
from pathlib import Path

import server

ROOT=Path(__file__).resolve().parents[1]

class CurriculumTests(unittest.TestCase):
    def test_every_business_question_has_exactly_one_exercise(self):
        questions=[]
        section=0
        for line in (ROOT/'docs/skillaju_business_questions.md').read_text(encoding='utf-8').splitlines():
            header=re.match(r'## (\d+)\.',line)
            if header: section=int(header[1])
            question=re.match(r'(\d+)\. (.+)',line)
            if question and section<=10:
                questions.append((f'{section}.{question[1]}',question[2]))
        exercises=list(server.EXERCISES.values())
        self.assertEqual(len(questions),75)
        self.assertEqual([(e['source_question'],e['business_question']) for e in exercises],questions)
        self.assertEqual(set(server.EXERCISES),set(server.REFERENCES))
        self.assertEqual(len({e['topic'] for e in exercises}),10)

    def test_all_references_are_accepted_and_have_declared_outputs(self):
        import sqlglot
        for eid,ref in server.REFERENCES.items():
            with self.subTest(exercise=eid):
                normalized=server.validate_sql(ref['sql'])
                self.assertEqual(sqlglot.parse_one(normalized,read='postgres').named_selects,server.EXERCISES[eid]['expected_output'])

class QuerySafetyTests(unittest.TestCase):
    def test_destructive_and_side_effect_queries_are_rejected(self):
        queries=[
            'DELETE FROM students', 'DROP TABLE courses',
            'SELECT 1; SELECT 2', 'SELECT * INTO copied FROM students',
            'WITH erased AS (DELETE FROM enrollments RETURNING *) SELECT * FROM erased',
            "SELECT set_config('statement_timeout','0',true)",
            'SELECT pg_sleep(100)', "SELECT pg_read_file('/etc/passwd')",
            'SELECT * FROM pg_catalog.pg_authid',
            'SELECT * FROM information_schema.tables',
            'SELECT * FROM other_schema.students',
            'SELECT * FROM public.students',
            "SELECT public.to_char(CURRENT_DATE,'YYYY')",
            'SELECT * FROM pg_ls_dir(\'/\')',
        ]
        for query in queries:
            with self.subTest(query=query),self.assertRaises(ValueError):
                server.validate_sql(query)

    def test_regular_ctes_and_semicolons_in_literals_are_accepted(self):
        self.assertTrue(server.validate_sql("WITH a AS (SELECT COUNT(*) AS n FROM students) SELECT n FROM a"))
        self.assertTrue(server.validate_sql("SELECT ';' AS punctuation"))

class ResultValidationTests(unittest.TestCase):
    @staticmethod
    def result(rows,columns=None,truncated=False):
        return {'columns':columns or ['value'],'rows':rows,'truncated':truncated}

    def test_equivalent_results_ignore_row_order_but_preserve_duplicates(self):
        a=self.result([[1],[2],[1]])
        b=self.result([[1],[1],[2]])
        self.assertTrue(server.compare_results(a,b,{})['passed'])
        self.assertFalse(server.compare_results(self.result([[1],[2],[2]]),b,{})['passed'])

    def test_wrong_values_aliases_and_truncated_results_fail(self):
        expected=self.result([[2]])
        for actual in [self.result([[3]]),self.result([[2]],['wrong']),self.result([[2]],truncated=True)]:
            self.assertFalse(server.compare_results(actual,expected,{})['passed'])

    def test_boolean_is_not_a_string_or_number(self):
        for value in ['True',1]:
            self.assertFalse(server.compare_results(self.result([[value]]),self.result([[True]]),{})['passed'])

    def test_numeric_comparison_preserves_large_integer_precision(self):
        self.assertTrue(server.compare_results(self.result([[1.0]]),self.result([[1]]),{})['passed'])
        self.assertFalse(server.compare_results(self.result([[9007199254740992]]),self.result([[9007199254740993]]),{})['passed'])

class ApiTests(unittest.TestCase):
    def setUp(self): self.client=server.app.test_client()

    def test_curriculum_does_not_expose_reference_answers(self):
        data=self.client.get('/api/exercises').get_json()
        self.assertEqual(len(data),75)
        self.assertTrue(all('reference_sql' not in row for row in data))
        self.assertEqual(self.client.get('/api/exercises/EXE-01/reference').status_code,200)
        self.assertEqual(self.client.get('/api/exercises/unknown/reference').status_code,404)

    def test_invalid_request_bodies_fail_before_database_access(self):
        self.assertEqual(self.client.post('/api/query',json=[]).status_code,400)
        self.assertEqual(self.client.post('/api/query',json={'sql':7}).status_code,400)
        self.assertEqual(self.client.post('/api/validate',json={'exercise_id':'wrong','sql':'SELECT 1'}).status_code,404)
        self.assertEqual(self.client.post('/api/query',json={'sql':'DROP TABLE students'}).status_code,422)

    def test_cors_allows_only_configured_origins(self):
        allowed=self.client.options('/api/query',headers={'Origin':'https://subhanaristiadi.github.io'})
        self.assertEqual(allowed.headers.get('Access-Control-Allow-Origin'),'https://subhanaristiadi.github.io')
        other=self.client.options('/api/query',headers={'Origin':'https://example.invalid'})
        self.assertNotIn('Access-Control-Allow-Origin',other.headers)

if __name__=='__main__': unittest.main()
