# Copyright 2015 Google Inc.
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

"""Define API Datasets."""

from __future__ import absolute_import

import six

from google.cloud._helpers import _datetime_from_microseconds
from google.cloud.bigquery.table import TableReference


class AccessEntry(object):
    """Represent grant of an access role to an entity.

    Every entry in the access list will have exactly one of
    ``userByEmail``, ``groupByEmail``, ``domain``, ``specialGroup`` or
    ``view`` set. And if anything but ``view`` is set, it'll also have a
    ``role`` specified. ``role`` is omitted for a ``view``, since
    ``view`` s are always read-only.

    See https://cloud.google.com/bigquery/docs/reference/rest/v2/datasets.

    :type role: str
    :param role: Role granted to the entity. One of

                 * ``'OWNER'``
                 * ``'WRITER'``
                 * ``'READER'``

                 May also be ``None`` if the ``entity_type`` is ``view``.

    :type entity_type: str
    :param entity_type: Type of entity being granted the role. One of
                        :attr:`ENTITY_TYPES`.

    :type entity_id: str
    :param entity_id: ID of entity being granted the role.

    :raises: :class:`ValueError` if the ``entity_type`` is not among
             :attr:`ENTITY_TYPES`, or if a ``view`` has ``role`` set or
             a non ``view`` **does not** have a ``role`` set.
    """

    ENTITY_TYPES = frozenset(['userByEmail', 'groupByEmail', 'domain',
                              'specialGroup', 'view'])
    """Allowed entity types."""

    def __init__(self, role, entity_type, entity_id):
        if entity_type not in self.ENTITY_TYPES:
            message = 'Entity type %r not among: %s' % (
                entity_type, ', '.join(self.ENTITY_TYPES))
            raise ValueError(message)
        if entity_type == 'view':
            if role is not None:
                raise ValueError('Role must be None for a view. Received '
                                 'role: %r' % (role,))
        else:
            if role is None:
                raise ValueError('Role must be set for entity '
                                 'type %r' % (entity_type,))

        self.role = role
        self.entity_type = entity_type
        self.entity_id = entity_id

    def __eq__(self, other):
        if not isinstance(other, AccessEntry):
            return NotImplemented
        return (
            self.role == other.role and
            self.entity_type == other.entity_type and
            self.entity_id == other.entity_id)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return '<AccessEntry: role=%s, %s=%s>' % (
            self.role, self.entity_type, self.entity_id)


class DatasetReference(object):
    """DatasetReferences are pointers to datasets.

    See
    https://cloud.google.com/bigquery/docs/reference/rest/v2/datasets

    :type project: str
    :param project: the ID of the project

    :type dataset_id: str
    :param dataset_id: the ID of the dataset
    """

    def __init__(self, project, dataset_id):
        self._project = project
        self._dataset_id = dataset_id

    @property
    def project(self):
        """Project ID of the dataset.

        :rtype: str
        :returns: the project ID.
        """
        return self._project

    @property
    def dataset_id(self):
        """Dataset ID.

        :rtype: str
        :returns: the dataset ID.
        """
        return self._dataset_id

    @property
    def path(self):
        """URL path for the dataset's APIs.

        :rtype: str
        :returns: the path based on project and dataset name.
        """
        return '/projects/%s/datasets/%s' % (self.project, self.dataset_id)

    def table(self, table_id):
        """Constructs a TableReference.

        :type table_id: str
        :param table_id: the ID of the table.

        :rtype: :class:`google.cloud.bigquery.table.TableReference`
        :returns: a TableReference for a table in this dataset.
        """
        return TableReference(self, table_id)


class Dataset(object):
    """Datasets are containers for tables.

    See
    https://cloud.google.com/bigquery/docs/reference/rest/v2/datasets

    :type dataset_id: str
    :param dataset_id: the ID of the dataset

    :type client: :class:`google.cloud.bigquery.client.Client`
    :param client: (Optional) A client which holds credentials and project
                   configuration for the dataset (which requires a project).

    :type access_entries: list of :class:`AccessEntry`
    :param access_entries: roles granted to entities for this dataset

    :type project: str
    :param project: (Optional) project ID for the dataset (defaults to
                    the project of the client).
    """

    _access_entries = None

    def __init__(self,
                 dataset_id,
                 client=None,
                 access_entries=(),
                 project=None):
        self._dataset_id = dataset_id
        self._client = client
        self._properties = {}
        # Let the @property do validation.
        self.access_entries = access_entries
        self._project = project or (client and client.project)

    @property
    def project(self):
        """Project bound to the dataset.

        :rtype: str
        :returns: the project (derived from the client).
        """
        return self._project

    @property
    def path(self):
        """URL path for the dataset's APIs.

        :rtype: str
        :returns: the path based on project and dataset ID.
        """
        return '/projects/%s/datasets/%s' % (self.project, self.dataset_id)

    @property
    def access_entries(self):
        """Dataset's access entries.

        :rtype: list of :class:`AccessEntry`
        :returns: roles granted to entities for this dataset
        """
        return list(self._access_entries)

    @access_entries.setter
    def access_entries(self, value):
        """Update dataset's access entries

        :type value: list of :class:`AccessEntry`
        :param value: roles granted to entities for this dataset

        :raises: TypeError if 'value' is not a sequence, or ValueError if
                 any item in the sequence is not an AccessEntry
        """
        if not all(isinstance(field, AccessEntry) for field in value):
            raise ValueError('Values must be AccessEntry instances')
        self._access_entries = tuple(value)

    @property
    def created(self):
        """Datetime at which the dataset was created.

        :rtype: ``datetime.datetime``, or ``NoneType``
        :returns: the creation time (None until set from the server).
        """
        creation_time = self._properties.get('creationTime')
        if creation_time is not None:
            # creation_time will be in milliseconds.
            return _datetime_from_microseconds(1000.0 * creation_time)

    @property
    def dataset_id(self):
        """Dataset ID.

        :rtype: str
        :returns: the dataset ID.
        """
        return self._dataset_id

    @property
    def full_dataset_id(self):
        """ID for the dataset resource, in the form "project_id:dataset_id".

        :rtype: str, or ``NoneType``
        :returns: the ID (None until set from the server).
        """
        return self._properties.get('id')

    @property
    def etag(self):
        """ETag for the dataset resource.

        :rtype: str, or ``NoneType``
        :returns: the ETag (None until set from the server).
        """
        return self._properties.get('etag')

    @property
    def modified(self):
        """Datetime at which the dataset was last modified.

        :rtype: ``datetime.datetime``, or ``NoneType``
        :returns: the modification time (None until set from the server).
        """
        modified_time = self._properties.get('lastModifiedTime')
        if modified_time is not None:
            # modified_time will be in milliseconds.
            return _datetime_from_microseconds(1000.0 * modified_time)

    @property
    def self_link(self):
        """URL for the dataset resource.

        :rtype: str, or ``NoneType``
        :returns: the URL (None until set from the server).
        """
        return self._properties.get('selfLink')

    @property
    def default_table_expiration_ms(self):
        """Default expiration time for tables in the dataset.

        :rtype: int, or ``NoneType``
        :returns: The time in milliseconds, or None (the default).
        """
        return self._properties.get('defaultTableExpirationMs')

    @default_table_expiration_ms.setter
    def default_table_expiration_ms(self, value):
        """Update default expiration time for tables in the dataset.

        :type value: int
        :param value: (Optional) new default time, in milliseconds

        :raises: ValueError for invalid value types.
        """
        if not isinstance(value, six.integer_types) and value is not None:
            raise ValueError("Pass an integer, or None")
        self._properties['defaultTableExpirationMs'] = value

    @property
    def description(self):
        """Description of the dataset.

        :rtype: str, or ``NoneType``
        :returns: The description as set by the user, or None (the default).
        """
        return self._properties.get('description')

    @description.setter
    def description(self, value):
        """Update description of the dataset.

        :type value: str
        :param value: (Optional) new description

        :raises: ValueError for invalid value types.
        """
        if not isinstance(value, six.string_types) and value is not None:
            raise ValueError("Pass a string, or None")
        self._properties['description'] = value

    @property
    def friendly_name(self):
        """Title of the dataset.

        :rtype: str, or ``NoneType``
        :returns: The name as set by the user, or None (the default).
        """
        return self._properties.get('friendlyName')

    @friendly_name.setter
    def friendly_name(self, value):
        """Update title of the dataset.

        :type value: str
        :param value: (Optional) new title

        :raises: ValueError for invalid value types.
        """
        if not isinstance(value, six.string_types) and value is not None:
            raise ValueError("Pass a string, or None")
        self._properties['friendlyName'] = value

    @property
    def location(self):
        """Location in which the dataset is hosted.

        :rtype: str, or ``NoneType``
        :returns: The location as set by the user, or None (the default).
        """
        return self._properties.get('location')

    @location.setter
    def location(self, value):
        """Update location in which the dataset is hosted.

        :type value: str
        :param value: (Optional) new location

        :raises: ValueError for invalid value types.
        """
        if not isinstance(value, six.string_types) and value is not None:
            raise ValueError("Pass a string, or None")
        self._properties['location'] = value

    @classmethod
    def from_api_repr(cls, resource, client):
        """Factory:  construct a dataset given its API representation

        :type resource: dict
        :param resource: dataset resource representation returned from the API

        :type client: :class:`google.cloud.bigquery.client.Client`
        :param client: Client which holds credentials and project
                       configuration for the dataset.

        :rtype: :class:`google.cloud.bigquery.dataset.Dataset`
        :returns: Dataset parsed from ``resource``.
        """
        if ('datasetReference' not in resource or
                'datasetId' not in resource['datasetReference']):
            raise KeyError('Resource lacks required identity information:'
                           '["datasetReference"]["datasetId"]')
        dataset_id = resource['datasetReference']['datasetId']
        dataset = cls(dataset_id, client=client)
        dataset._set_properties(resource)
        return dataset

    @staticmethod
    def _parse_access_entries(access):
        """Parse a resource fragment into a set of access entries.

        ``role`` augments the entity type and present **unless** the entity
        type is ``view``.

        :type access: list of mappings
        :param access: each mapping represents a single access entry.

        :rtype: list of :class:`AccessEntry`
        :returns: a list of parsed entries.
        :raises: :class:`ValueError` if a entry in ``access`` has more keys
                 than ``role`` and one additional key.
        """
        result = []
        for entry in access:
            entry = entry.copy()
            role = entry.pop('role', None)
            entity_type, entity_id = entry.popitem()
            if len(entry) != 0:
                raise ValueError('Entry has unexpected keys remaining.', entry)
            result.append(
                AccessEntry(role, entity_type, entity_id))
        return result

    def _set_properties(self, api_response):
        """Update properties from resource in body of ``api_response``

        :type api_response: dict
        :param api_response: response returned from an API call.
        """
        self._properties.clear()
        cleaned = api_response.copy()
        access = cleaned.pop('access', ())
        self.access_entries = self._parse_access_entries(access)
        if 'creationTime' in cleaned:
            cleaned['creationTime'] = float(cleaned['creationTime'])
        if 'lastModifiedTime' in cleaned:
            cleaned['lastModifiedTime'] = float(cleaned['lastModifiedTime'])
        if 'defaultTableExpirationMs' in cleaned:
            cleaned['defaultTableExpirationMs'] = int(
                cleaned['defaultTableExpirationMs'])
        self._properties.update(cleaned)

    def _build_access_resource(self):
        """Generate a resource fragment for dataset's access entries."""
        result = []
        for entry in self.access_entries:
            info = {entry.entity_type: entry.entity_id}
            if entry.role is not None:
                info['role'] = entry.role
            result.append(info)
        return result

    def _build_resource(self):
        """Generate a resource for ``create`` or ``update``."""
        resource = {
            'datasetReference': {
                'projectId': self.project, 'datasetId': self.dataset_id},
        }
        if self.default_table_expiration_ms is not None:
            value = self.default_table_expiration_ms
            resource['defaultTableExpirationMs'] = value

        if self.description is not None:
            resource['description'] = self.description

        if self.friendly_name is not None:
            resource['friendlyName'] = self.friendly_name

        if self.location is not None:
            resource['location'] = self.location

        if len(self.access_entries) > 0:
            resource['access'] = self._build_access_resource()

        return resource

    def table(self, table_id):
        """Constructs a TableReference.

        :type table_id: str
        :param table_id: the ID of the table.

        :rtype: :class:`google.cloud.bigquery.table.TableReference`
        :returns: a TableReference for a table in this dataset.
        """
        return TableReference(self, table_id)
