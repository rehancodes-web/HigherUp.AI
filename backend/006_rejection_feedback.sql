-- Run once in the SAP HANA schema containing JOB_APPLICATION.
-- Stores role-specific development feedback created when a recruiter passes on an application.
ALTER TABLE JOB_APPLICATION ADD (REJECTION_FEEDBACK NCLOB);
