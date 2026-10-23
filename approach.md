# Technical Approach — CT-200 Document Intelligence API

## 1. Architecture

The application uses FastAPI to expose document-processing APIs, PyMuPDF to extract PDF text, SQLAlchemy to persist document versions and nodes, and SQLite as the database.

The pipeline is:

PDF input → Text extraction → Heading detection → Section hierarchy → Content hashing → Database storage → Search and version comparison → QA generation.

## 2. Data Model

- **DocumentVersion:** Stores the version name and source filename.
- **DocumentNode:** Stores a heading, hierarchy level, body text, parent relationship, and content hash.
- **NamedSelection:** Stores a named selection associated with a specific document version.
- **GeneratedQA:** Stores generated QA ideas and a snapshot of their source content.

The current schema uses SQLite and JSON-encoded text fields for selections and generated output.

## 3. Parsing Decisions

The parser uses PyMuPDF to extract text page by page. It recognizes numbered headings and some short, uppercase lines as possible headings.

Numbered headings are assigned hierarchy levels according to their numbering depth. Other lines are treated as body text.

### Known parsing limitations
- A numbered paragraph may be mistaken for a heading.
- A short uppercase line may be incorrectly classified as a heading.
- Tables may lose their original row and column relationships.
- Figures and captions are not fully reconstructed.
- Repeated headings can create ambiguous parent relationships.

These limitations require testing against both supplied manual versions.

## 4. Content Matching Strategy

The application normalizes whitespace and calculates a SHA-256 hash of the normalized text.

Identical hashes indicate identical normalized body text. Different hashes indicate a content difference.

The current version comparison also uses heading and occurrence order to compare sections. This is a simple initial strategy, not a guaranteed permanent logical identity system.

### Failure modes
- A renamed heading may appear as a removed section and an added section.
- Repeated headings may be matched incorrectly.
- A changed heading may hide the relationship between two logically identical sections.
- Whitespace normalization does not identify semantic equivalence.

A stronger implementation should use parent context, section numbering, content similarity, and explicit matching confidence.

## 5. QA Generation and Validation

The current generator returns predefined QA examples validated with Pydantic. It checks that the result contains between three and five test ideas and that each test has the required fields.

This is a mock implementation, not a live LLM integration. A production version should use a real LLM, validate its structured response, retry malformed output within a bounded limit, and record the exact source snapshot.

## 6. Staleness and Impact Detection

Generated QA records store the source node identifiers, headings, hashes, and body text.

The API can compare source hashes and report whether content appears current or changed. Cross-version checks are limited by the current heading-based matching strategy.

A changed hash does not establish that a change is clinically significant. A production system should separately detect changes to thresholds, units, warnings, and safety-critical instructions.

## 7. Testing Strategy

The project includes parser and content-hash unit tests. Further tests should cover:

- Duplicate headings under different parents.
- Version comparison for unchanged and modified sections.
- Invalid PDF files and missing inputs.
- Named selections pinned to the correct version.
- Malformed QA responses and duplicate generation requests.
- Stale QA after source changes.

## 8. Decision Log

### Most likely silent failure and detection
A heading can be classified incorrectly, causing incorrect hierarchy. Detect this through representative PDF fixtures, parent-child assertions, and manual inspection of extracted sections.

### Where simplicity was chosen over correctness
The initial parser uses text-based heading heuristics instead of a full layout-aware document parser. Complex tables and repeated headings are likely areas of failure.

### Unhandled input and intended behavior
A scanned PDF with no extractable text may produce no usable sections. The application should reject it with a clear validation error and explain that OCR support is required.

## 9. Future Improvements

- Add OCR for scanned documents.
- Improve layout-aware table and figure extraction.
- Introduce reliable cross-version logical node matching.
- Add real LLM integration, bounded retries, and idempotent generation.
- Detect critical threshold and safety-instruction changes.
- Expand automated and end-to-end testing.
