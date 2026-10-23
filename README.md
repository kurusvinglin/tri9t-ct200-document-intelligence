# Tri9T AI Engineering Internship
## CT-200 Document Intelligence API

### Project Overview
This project extracts structured information from versions of a CardioTrack CT-200 Home Blood Pressure Monitor manual. It provides APIs to browse document sections, search content, compare versions, create version-pinned selections, and generate QA test ideas.

### Technology Stack
- Python
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- PyMuPDF
- Pytest

### Project Structure
```text
tri9t-ct200-github/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── parser.py
│   ├── versioning.py
│   └── generation.py
├── data/
│   ├── ct200_manual.pdf
│   └── ct200_manual_v2.pdf
├── tests/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### Setup
1. Install Python 3.12 or a compatible version.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Place the supplied PDF files inside the `data/` directory.
5. Start the API:

```bash
python -m uvicorn app.main:app --reload
```

6. Open `http://127.0.0.1:8000/docs` to explore the API.

### Testing

Run the automated tests:

```bash
python -m pytest -v
```

### Document Version Workflow
1. Ingest the first manual version.
2. Ingest the second manual version under a separate version name.
3. Compare the versions to identify added, removed, unchanged, and modified sections.
4. Create a named selection pinned to a specific version.
5. Generate QA test ideas from the selected content.
6. Check whether generated tests have become stale after document changes.

### Limitations
The parser uses heading heuristics and may not reliably reconstruct every table, figure, caption, or unusual layout. The current QA generator uses predefined examples rather than a live LLM. Version matching and staleness detection require further validation, especially for duplicate headings and critical numerical changes.

### Future Improvements
- Integrate a real LLM with structured-output validation and bounded retries.
- Improve table, figure, and caption extraction.
- Strengthen logical node matching across document versions.
- Add more regression and end-to-end tests.
- Improve detection of clinically significant changes.

## QA Test Generation

The API generates structured QA test ideas from a selected section of a specific manual version. Each test includes a title, steps, and an expected result.

The current implementation uses a deterministic mock generator with Pydantic validation. It does not call a real AI language model because no API key is configured.

### Validation
- Rejects empty input.
- Requires 3 to 5 test ideas.
- Validates the title, steps, and expected result of each test.
- Includes automated tests for empty input and output structure.

### Known Limitations
- Real LLM integration is not implemented.
- Retrying malformed LLM responses is not implemented.
- The generated examples are placeholders and must not be represented as real LLM-generated results.

### Run Tests

```bash
python -m pytest -v
```
