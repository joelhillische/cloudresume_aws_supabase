# README

This README outlines the RAGOM (Retrieve A Golden Of The Midwest) AWS Step Functions, Lambdas, and the Supabase backend.

Overall the idea is to use the AWS Step Function to grab from the RAGOM Google Directory and feed users, groups, and latitude / longitudes into the Supabase backend so WeWeb can correctly display the information.

## Google

You need to add one OClient user under Google https://console.cloud.google.com/apis/credentials under the Service Accounts header.

You need to grab the Service Account json and copy that into the Systems Manager under the Parameter Store and copy and paste that into the key /ragom/google/service_account_json.

### Google Keys

There are keys for the map, and geocoding `/ragom/google/geocoding_key`. The map key is not present with AWS System Manager it is just present in WeWeb.

#### Map Key

The map key is just for the WeWeb Google Map integration.

#### Geocoding Key

The map key takes the address and populates a latitude and longitude.

## AWS

### Tailing CloudWatch Logs

`aws logs tail  /aws/lambda/ragom-sandbox-get-users --follow`
`aws logs tail  /aws/lambda/ragom-sandbox-get-groups --follow`
