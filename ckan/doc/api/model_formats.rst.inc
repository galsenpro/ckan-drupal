Model Formats
~~~~~~~~~~~~~

Here are the data formats for the Model API.

.. include:: model_formats_table.rst.inc

.. |format-package-ref| replace:: Package-Id

.. |format-package-register| replace:: [ |format-package-ref|, |format-package-ref|, |format-package-ref|, ... ]

.. |format-package-entity| replace:: { id: Uuid, name: Name-String, title: String, version: String, url: String, resources: [ Resource, Resource, ...], author: String, author_email: String, maintainer: String, maintainer_email: String, license_id: String, tags: Tag-List, notes: String, extras: { Name-String: String, ... } }

.. |format-group-ref| replace:: Group-Id

.. |format-group-register| replace:: [ |format-group-ref|, |format-group-ref|, |format-group-ref|, ... ]

.. |format-group-entity| replace:: { name: Name-String, title: String, description: String, packages: Package-List }


To send request data, create the JSON-format string (encode in UTF8) put it in the request body and send it using PUT or POST.

Response data will be in the response body in JSON format.

Notes:

 * When you update an object, fields that you don't supply will remain as they were before.

 * To delete an 'extra' key-value pair, supply the key with JSON value: ``null``

 * When you read a package then some additional information is supplied that cannot current be adjusted throught the CKAN API. This includes info on Package Relationship ('relationships'), Group membership ('groups'), ratings ('ratings_average' and 'ratings_count'), full URL of the package in CKAN ('ckan_url') and Package ID ('id'). This is purely a convenience for clients, and only forms part of the Package on GET.
