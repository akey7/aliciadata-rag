CREATE OR REPLACE VIEW chunk_citations AS
(
    WITH paper_chunk_citation_counts AS (
        WITH citation_counts AS (
            SELECT 
                chunk_id,
                COUNT(*) AS chunk_citation_count
            FROM 
                chunk_retrievals
            GROUP BY 
                chunk_id
        )
        SELECT
            cp.paper_uuid4,
            cc.chunk_id, 
            cc.chunk_citation_count
        FROM 
            chunks_papers cp
        INNER JOIN 
            citation_counts cc 
        ON 
            cp.id = cc.chunk_id
    )
    SELECT 
        p.title,
        pccc.chunk_id,
        pccc.chunk_citation_count 
    FROM 
        papers p
    INNER JOIN 
        paper_chunk_citation_counts pccc 
    ON 
        p.uuid4 = pccc.paper_uuid4
    ORDER BY 
        chunk_citation_count DESC
);
