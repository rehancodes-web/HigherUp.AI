-- Run once in the SAP HANA schema containing CANDIDATE_PROFILE.
-- The talent pool: every resume the AI has read and summarised into a one-page profile.
-- Recruiters see these in the Talent Deck. Used by talent.py and import_resumes.py.

CREATE COLUMN TABLE TALENT_PROFILE (
    PROFILE_ID NVARCHAR(36) PRIMARY KEY,
    SOURCE_FILE NVARCHAR(255) NOT NULL,     -- the resume's file name; uploading it again replaces the profile
    CANDIDATE_NAME NVARCHAR(200),
    PROFILE_JSON BLOB NOT NULL,             -- the one-page summary (UTF-8 JSON)
    CREATED_AT TIMESTAMP NOT NULL
);
CREATE INDEX TALENT_PROFILE_SOURCE_IDX ON TALENT_PROFILE (SOURCE_FILE);
