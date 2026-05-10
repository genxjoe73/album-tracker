# Inventory Export [](#page:inventory-export)

## Export your inventory [](#page:inventory-export,header:inventory-export-export-your-inventory)

Export your inventory

[POST](#page:inventory-export,header:inventory-export-export-your-inventory-post)

`/inventory/export`

Request an export of your inventory as a CSV.

- **Response  `200`**
  Toggle

- 

  ##### Headers

      Content-Type: application/json
      Location: https://api.discogs.com/inventory/export/599632

- **Response  `401`**
  Toggle

- 

  ##### Headers

      Content-Type: application/json

- **Response  `409`**
  Toggle

- 

  ##### Headers

      Content-Type: application/json

## Get recent exports [](#page:inventory-export,header:inventory-export-get-recent-exports)

Get recent exports

[GET](#page:inventory-export,header:inventory-export-get-recent-exports-get)

`/inventory/export`

Get a list of all recent exports of your inventory. Accepts [Pagination parameters](#page:home,header:home-pagination).

- **Response  `200`**
  Toggle

- 

  ##### Headers

      Content-Type: application/json

  ##### Body

      {
        "items": [
          {
            "status": "success",
            "created_ts": "2018-09-27T12:59:02",
            "url": "https://api.discogs.com/inventory/export/599632",
            "finished_ts": "2018-09-27T12:59:02",
            "download_url": "https://api.discogs.com/inventory/export/599632/download",
            "filename": "cburmeister-inventory-20180927-1259.csv",
            "id": 599632
          }
        ],
        "pagination": {
          "per_page": 50,
          "items": 15,
          "page": 1,
          "urls": {},
          "pages": 1
        }
      }

- **Response  `401`**
  Toggle

- 

  ##### Headers

      Content-Type: application/json

## Get an export [](#page:inventory-export,header:inventory-export-get-an-export)

Get an export

[GET](#page:inventory-export,header:inventory-export-get-an-export-get)

`/inventory/export/{id}`

Get details about the status of an inventory export.

- **Parameters**

- id  
  `number` (required) 

  Id of the export.

&nbsp;

- **Request**
  Toggle

- 

  ##### Headers

      Content-Type: multipart/form-data
      If-Modified-Since: Thu, 27 Sep 2018 12:50:39 GMT

- **Response  `200`**
  Toggle

- 

  ##### Headers

      Content-Type: application/json
      Last-Modified: Thu, 27 Sep 2018 12:59:02 GMT

  ##### Body

      {
        "status": "success",
        "created_ts": "2018-09-27T12:50:39",
        "url": "https://api.discogs.com/inventory/export/599632",
        "finished_ts": "2018-09-27T12:59:02",
        "download_url": "https://api.discogs.com/inventory/export/599632/download",
        "filename": "cburmeister-inventory-20180927-1259.csv",
        "id": 599632
      }

- **Response  `304`**

- **Response  `401`**
  Toggle

- 

  ##### Headers

      Content-Type: application/json

- **Response  `404`**
  Toggle

- 

  ##### Headers

      Content-Type: application/json

## Download an export [](#page:inventory-export,header:inventory-export-download-an-export)

Download an export

[GET](#page:inventory-export,header:inventory-export-download-an-export-get)

`/inventory/export/{id}/download`

Download the results of an inventory export.

- **Parameters**

- id  
  `number` (required) 

  Id of the export.

&nbsp;

- **Response  `200`**
  Toggle

- 

  ##### Headers

      Content-Type: text/csv; charset=utf-8
      Content-Disposition: attachment; filename=cburmeister-inventory-20180927-1259.csv

- **Response  `401`**
  Toggle

- 

  ##### Headers

      Content-Type: application/json

- **Response  `404`**
  Toggle

- 

  ##### Headers

      Content-Type: application/json

[Next ](#page:inventory-upload)[ Previous](#page:marketplace)

------------------------------------------------------------------------
