# Knowledge Fabric Integration

Intent Fabric consumes evidence packages produced by Knowledge Fabric.

Input contract:

```text
query_text
items[] { chunk_id, document_uri, snippet, score, metadata }
retrieval_summary
```

Intent Fabric treats this as read-only planning context and never performs runtime execution.
