# -*- coding: utf-8 -*-
# Copyright Commvault Systems, Inc.
# SPDX-License-Identifier: Apache-2.0

"""Helpers for entity tag APIs not exposed by the SDK's Tags class."""


def request(commcell, method, path, payload=None):
    """Send an authenticated SDK request and surface HTTP and API errors."""
    url = commcell._web_service.rstrip('/') + '/' + path.lstrip('/')
    flag, response = commcell._cvpysdk_object.make_request(method, url, payload)
    if not flag:
        raise ValueError("Tag API request failed: {0}".format(
            commcell._update_response_(response.text)))

    data = response.json()
    if not isinstance(data, dict) or not data:
        raise ValueError("Tag API returned an empty or invalid response")

    errors = [data]
    if 'error' in data:
        if not isinstance(data['error'], dict):
            raise ValueError("Tag API returned an invalid error object")
        errors.append(data['error'])
    if 'errList' in data:
        if not isinstance(data['errList'], list):
            raise ValueError("Tag API returned an invalid error list")
        errors.extend(data['errList'])
    for error in errors:
        if not isinstance(error, dict):
            raise ValueError("Tag API returned an invalid error entry")
        code = error.get('errorCode', 0)
        message = error.get('errorMessage') or error.get('errLogMessage')
        if code not in (0, '0', None) or message:
            raise ValueError("Tag API error {0}: {1}".format(code, message or 'Unknown error'))
    return data


def client_tags(commcell, client_id):
    """Read tags for a client entity, rejecting malformed success responses."""
    data = request(commcell, 'GET', 'Tags/CLIENT_ENTITY/{0}'.format(client_id))
    entities = data.get('tags')
    if not isinstance(entities, list):
        raise ValueError("Tag API response is missing the tags list")
    tags = []
    for entity in entities:
        if not isinstance(entity, dict):
            raise ValueError("Tag API returned an invalid entity")
        if str(entity.get('entityId')) != str(client_id) or entity.get('entityType') not in (3, '3'):
            raise ValueError("Tag API returned tags for an unexpected entity")
        entries = entity.get('tag')
        if not isinstance(entries, list):
            raise ValueError("Tag API response is missing the entity tag list")
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get('name'), str):
                raise ValueError("Tag API returned an invalid tag")
            tags.append(entry)
    return tags


def validate_names(names):
    """Reject empty tag names before issuing mutations."""
    if any(not name.strip() for name in names):
        raise ValueError("Tag names must not be empty or whitespace")
