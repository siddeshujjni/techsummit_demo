-- Prerequisites: UC permissions needed before syncing
-- Run these as a catalog admin or ask one of: siddesh.ujjni, nasir.dakri, devanshu.pandey

GRANT USE CATALOG ON CATALOG techsummit_27 TO `ron.guerrero@databricks.com`;
GRANT USE SCHEMA ON SCHEMA techsummit_27.meridian_bank TO `ron.guerrero@databricks.com`;
GRANT SELECT ON SCHEMA techsummit_27.meridian_bank TO `ron.guerrero@databricks.com`;
