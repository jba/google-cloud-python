# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import copy
import unittest

from google.cloud.bigquery.external_config import ExternalConfig


class TestExternalConfig(unittest.TestCase):

    SOURCE_URIS = ['gs://foo', 'gs://bar']

    BASE_RESOURCE = {
        'sourceUris': SOURCE_URIS,
        'sourceFormat': 'sourceFormat',
        'maxBadRecords': 17,
        'autodetect': True,
        'ignoreUnknownValues': False,
        'compression': 'compression',
    }

    def test_api_repr_base(self):
        from google.cloud.bigquery.schema import SchemaField

        resource = copy.deepcopy(self.BASE_RESOURCE)
        ec = ExternalConfig.from_api_repr(resource)
        self._verify_base(ec)
        self.assertIsNone(ec.schema)
        self.assertIsNone(ec.options)

        got_resource = ec.to_api_repr()
        self.assertEqual(got_resource, self.BASE_RESOURCE)

        resource = _copy_and_update(self.BASE_RESOURCE, {
            'schema': {
                'fields': [
                    {
                        'name': 'full_name',
                        'type': 'STRING',
                        'mode': 'REQUIRED',
                    },
                ],
            },
        })
        want_resource = copy.deepcopy(resource)
        ec = ExternalConfig.from_api_repr(resource)
        self._verify_base(ec)
        self.assertEqual(ec.schema,
                         [SchemaField('full_name', 'STRING', mode='REQUIRED')])
        self.assertIsNone(ec.options)

        got_resource = ec.to_api_repr()
        self.assertEqual(got_resource, want_resource)

    def _verify_base(self, ec):
        self.assertEqual(ec.autodetect, True)
        self.assertEqual(ec.compression, 'compression')
        self.assertEqual(ec.ignore_unknown_values, False)
        self.assertEqual(ec.max_bad_records, 17)
        self.assertEqual(ec.source_format, 'sourceFormat')
        self.assertEqual(ec.source_uris, self.SOURCE_URIS)

    def test_api_repr_sheets(self):
        from google.cloud.bigquery.external_config import GoogleSheetsOptions

        resource = _copy_and_update(self.BASE_RESOURCE, {
            'googleSheetsOptions': {'skipLeadingRows': '123'},
            })
        want_resource = copy.deepcopy(resource)

        ec = ExternalConfig.from_api_repr(resource)

        self._verify_base(ec)
        self.assertIsInstance(ec.options, GoogleSheetsOptions)
        self.assertEqual(ec.options.skip_leading_rows, 123)

        got_resource = ec.to_api_repr()

        self.assertEqual(got_resource, want_resource)

        del want_resource['googleSheetsOptions']['skipLeadingRows']
        ec = ExternalConfig.from_api_repr(copy.deepcopy(want_resource))
        self.assertIsNone(ec.options.skip_leading_rows)
        got_resource = ec.to_api_repr()
        self.assertEqual(got_resource, want_resource)

    def test_api_repr_csv(self):
        from google.cloud.bigquery.external_config import CSVOptions

        resource = _copy_and_update(self.BASE_RESOURCE, {
            'csvOptions': {
                'fieldDelimiter': 'fieldDelimiter',
                'skipLeadingRows': '123',
                'quote': 'quote',
                'allowQuotedNewlines': True,
                'allowJaggedRows': False,
                'encoding': 'encoding',
            },
        })
        want_resource = copy.deepcopy(resource)

        ec = ExternalConfig.from_api_repr(resource)

        self._verify_base(ec)
        self.assertIsInstance(ec.options, CSVOptions)
        self.assertEqual(ec.options.field_delimiter, 'fieldDelimiter')
        self.assertEqual(ec.options.skip_leading_rows, 123)
        self.assertEqual(ec.options.quote_character, 'quote')
        self.assertEqual(ec.options.allow_quoted_newlines, True)
        self.assertEqual(ec.options.allow_jagged_rows, False)
        self.assertEqual(ec.options.encoding, 'encoding')

        got_resource = ec.to_api_repr()

        self.assertEqual(got_resource, want_resource)

        del want_resource['csvOptions']['skipLeadingRows']
        ec = ExternalConfig.from_api_repr(copy.deepcopy(want_resource))
        self.assertIsNone(ec.options.skip_leading_rows)
        got_resource = ec.to_api_repr()
        self.assertEqual(got_resource, want_resource)

    def test_api_repr_bigtable(self):
        from google.cloud.bigquery.external_config import BigtableOptions
        from google.cloud.bigquery.external_config import BigtableColumnFamily

        QUALIFIER_ENCODED = base64.standard_b64encode(b'q').decode('ascii')
        resource = _copy_and_update(self.BASE_RESOURCE, {
            'bigtableOptions': {
                'ignoreUnspecifiedColumnFamilies': True,
                'readRowkeyAsString': False,
                'columnFamilies': [
                    {
                        'familyId': 'familyId',
                        'type': 'type',
                        'encoding': 'encoding',
                        'columns': [
                            {
                                'qualifierString': 'q',
                                'fieldName': 'fieldName1',
                                'type': 'type1',
                                'encoding': 'encoding1',
                                'onlyReadLatest': True,
                            },
                            {
                                'qualifierEncoded': QUALIFIER_ENCODED,
                                'fieldName': 'fieldName2',
                                'type': 'type2',
                                'encoding': 'encoding2',
                            },

                        ],
                        'onlyReadLatest': False,
                    }
                ],
            },
        })
        want_resource = copy.deepcopy(resource)

        ec = ExternalConfig.from_api_repr(resource)

        self._verify_base(ec)
        self.assertIsInstance(ec.options, BigtableOptions)
        self.assertEqual(ec.options.ignore_unspecified_column_families, True)
        self.assertEqual(ec.options.read_rowkey_as_string, False)
        self.assertEqual(len(ec.options.column_families), 1)
        fam1 = ec.options.column_families[0]
        self.assertIsInstance(fam1, BigtableColumnFamily)
        self.assertEqual(fam1.family_id, 'familyId')
        self.assertEqual(fam1.type, 'type')
        self.assertEqual(fam1.encoding, 'encoding')
        self.assertEqual(len(fam1.columns), 2)
        col1 = fam1.columns[0]
        self.assertEqual(col1.qualifier_string, 'q')
        self.assertEqual(col1.field_name, 'fieldName1')
        self.assertEqual(col1.type, 'type1')
        self.assertEqual(col1.encoding, 'encoding1')
        col2 = ec.options.column_families[0].columns[1]
        self.assertEqual(col2.qualifier_encoded, b'q')
        self.assertEqual(col2.field_name, 'fieldName2')
        self.assertEqual(col2.type, 'type2')
        self.assertEqual(col2.encoding, 'encoding2')

        got_resource = ec.to_api_repr()

        self.assertEqual(got_resource, want_resource)

    def test_bad_schema(self):
        ec = ExternalConfig()
        with self.assertRaises(ValueError):
            ec.schema = [1]


def _copy_and_update(d, u):
    d = copy.deepcopy(d)
    d.update(u)
    return d
