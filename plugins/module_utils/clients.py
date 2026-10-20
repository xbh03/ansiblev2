# -*- coding: utf-8 -*-
# Copyright Commvault Systems, Inc.
# SPDX-License-Identifier: Apache-2.0

"""Shared lookup for existing client entities."""


def get_client(commcell, client=None, client_id=None):
    """Resolve exactly one client name or positive ID through CVPySDK."""
    if (client is None) == (client_id is None):
        raise ValueError("Specify exactly one of client or client_id")
    if client_id is not None:
        if client_id <= 0:
            raise ValueError("client_id must be a positive integer")
        identifier = client_id
    else:
        if not client.strip():
            raise ValueError("Client name must not be empty or whitespace")
        identifier = client

    resolved = commcell.clients.get(identifier)
    if client_id is not None and int(resolved.client_id) != client_id:
        raise ValueError("SDK lookup returned a different client ID than requested")
    return resolved
