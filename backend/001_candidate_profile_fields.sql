-- Run once in SAP HANA Database Explorer against the schema containing CANDIDATE_PROFILE.
-- These fields hold structured candidate profile data; uploaded files remain in object storage.
ALTER TABLE CANDIDATE_PROFILE ADD (
    HEADLINE NVARCHAR(200),
    PHONE NVARCHAR(40),
    CITY NVARCHAR(100),
    LOOKING_FOR NVARCHAR(100),
    AVAILABLE NVARCHAR(100),
    EDUCATION NVARCHAR(250),
    LINKEDIN NVARCHAR(500),
    GITHUB NVARCHAR(500),
    PORTFOLIO NVARCHAR(500),
    BIO NVARCHAR(1200)
);
