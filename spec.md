Software Specification: Harvard Reference Validator and Verifier

This document outlines the software specification for a Python script designed to validate and verify Harvard references according to the "Cite Them Right" (CTR) format. The script will leverage free APIs and search tools to check the authenticity and existence of the cited sources.

1. Introduction
The purpose of this script is to assist researchers, students, and academics in ensuring the accuracy and validity of their Harvard-style reference lists. It will automate the tedious process of manually checking reference formatting and source availability, providing a concise report for each entry and an overall summary.

2. Goals
To validate Harvard reference formatting against "Cite Them Right" guidelines.

To verify the existence and authenticity of cited sources using accessible online tools and APIs.

To provide clear, detailed feedback for each reference.

To generate a summary of the validation and verification process.

3. Input Specification
The script will accept a list of Harvard references. This input can be provided in one of the following ways:

Command-line arguments: A file path to a text file containing one reference per line.

Direct string input: A multi-line string containing references. (Less preferred for large lists, but useful for testing).

Example Input (text file references.txt):

Smith, J. (2020) 'The Future of AI', Journal of Advanced Robotics, 15(2), pp. 123-145. doi:10.1000/j.ar.2020.02.001
Jones, A. (2019) Understanding Climate Change. London: Green Press.
Brown, C. (2021) Digital Transformation. Available at: https://www.techinsights.com/digital-transformation-report (Accessed: 15 July 2025).

4. Output Specification
The script will produce a concise output for each reference, followed by a summary. The output should be human-readable and suitable for display in a console or a simple report file.

4.1 Per-Reference Output
For each reference provided, the output will include:

Original Reference: The full reference as provided in the input.

CTR Format Valid: Yes or No.

Source Verified: Yes, No, or Partial (if some checks passed but others failed or were inconclusive).

Checks Performed: A list detailing each specific check made (e.g., "Checked URL existence", "Resolved DOI", "Searched journal for article").

Verification Details: Specific outcomes of each check (e.g., "URL reachable", "DOI resolved to 'The Future of AI'", "Article found in Journal of Advanced Robotics, Vol 15, Issue 2").

Clickable Link: A direct, clickable URL to the verified source, if found during the verification process. If multiple links are found, the most relevant one should be provided. If no direct link is available, state "No direct link found."

Example Per-Reference Output:

--- Reference 1 ---
Original Reference: Smith, J. (2020) 'The Future of AI', Journal of Advanced Robotics, 15(2), pp. 123-145. doi:10.1000/j.ar.2020.02.001
CTR Format Valid: Yes
Source Verified: Yes
Checks Performed:
  - Identified reference type: Journal Article.
  - Extracted DOI: 10.1000/j.ar.2020.02.001.
  - Resolved DOI using CrossRef API.
  - Verified title 'The Future of AI' and author 'J. Smith' against DOI resolution.
Verification Details:
  - DOI resolved successfully to "The Future of AI" by J. Smith.
  - Journal: Journal of Advanced Robotics, Volume 15, Issue 2, Pages 123-145.
Clickable Link: https://doi.org/10.1000/j.ar.2020.02.001

--- Reference 2 ---
Original Reference: Jones, A. (2019) Understanding Climate Change. London: Green Press.
CTR Format Valid: Yes
Source Verified: Partial
Checks Performed:
  - Identified reference type: Book.
  - Attempted ISBN lookup (no ISBN found in reference).
  - Performed general web search for "Understanding Climate Change A. Jones Green Press".
Verification Details:
  - No direct ISBN for lookup.
  - General web search found multiple results, but no definitive, direct link to the specific edition.
Clickable Link: No direct link found. (Suggest: https://www.goodreads.com/book/show/12345678-understanding-climate-change if a close match is found)

--- Reference 3 ---
Original Reference: Brown, C. (2021) Digital Transformation. Available at: https://www.techinsights.com/digital-transformation-report (Accessed: 15 July 2025).
CTR Format Valid: No (Reason: 'Accessed' date format incorrect, should be '15 July 2025' not '15 July 2025')
Source Verified: Yes
Checks Performed:
  - Identified reference type: Website.
  - Checked URL accessibility.
  - Verified presence of keywords "Digital Transformation" on the page.
Verification Details:
  - URL is accessible (HTTP 200 OK).
  - Keywords "Digital Transformation" found on the webpage.
Clickable Link: https://www.techinsights.com/digital-transformation-report

4.2 Summary Output
At the end of the report, a brief summary will be provided:

Total references checked: [Number]

References with valid CTR format: [Number]

References verified correct (format and existence): [Number]

Example Summary Output:

--- Summary ---
Total references checked: 3
References with valid CTR format: 2
References verified correct: 2

5. Functional Requirements
5.1 Reference Parsing and Type Identification
FR1.1: The script shall parse each input line to identify distinct reference components (author, year, title, journal/publisher, volume, issue, pages, DOI, URL, access date).

FR1.2: The script shall attempt to identify the type of reference (e.g., book, journal article, website, conference paper, report) based on its structure and keywords.

5.2 Harvard Cite Them Right (CTR) Format Validation
FR2.1: The script shall implement rules for validating the formatting of common Harvard CTR reference types. This includes:

Author name format (e.g., Surname, Initials.).

Year format (e.g., (YYYY)).

Title capitalization and italics based on reference type.

Journal/publisher details.

Volume, issue, page number formats.

DOI format.

URL and access date format for online sources.

FR2.2: For any format invalidation, the script shall provide a specific reason (e.g., "Incorrect year format", "Missing author initials").

5.3 Source Verification
FR3.1: Website Verification:

FR3.1.1: If a URL is present, the script shall attempt to access the URL (HTTP GET request).

FR3.1.2: The script shall check the HTTP status code (e.g., 200 OK for success, report others).

FR3.1.3: (Optional but desirable) The script shall attempt to extract content from the page and search for keywords (e.g., title, author, key phrases from the reference) to confirm relevance.

FR3.2: DOI Resolution:

FR3.2.1: If a DOI is present, the script shall use a free DOI resolution API (e.g., CrossRef API) to retrieve metadata associated with the DOI.

FR3.2.2: The script shall compare the retrieved metadata (e.g., title, authors, journal, year) with the information provided in the reference to confirm a match.

FR3.3: Journal Article/Paper Verification (without DOI):

FR3.3.1: If a journal name, volume, issue, and page numbers are present but no DOI, the script shall use general academic search APIs (e.g., Google Scholar if possible via a programmatic interface, or other open academic databases) to search for the article.

FR3.3.2: The script shall verify if the article exists in the specified journal and matches the provided author(s) and title.

FR3.4: Book Verification:

FR3.4.1: If an ISBN is present (extracted or inferred), the script shall use an ISBN lookup API (e.g., Open Library Books API, Google Books API - check free tier limitations) to retrieve book details.

FR3.4.2: The script shall compare retrieved details (title, author, publisher, year) with the reference.

FR3.4.3: If no ISBN or ISBN lookup fails, the script shall perform a general web search (e.g., using a search engine API) for the book title, author, and publisher.

5.4 Error Handling and Reporting
FR4.1: The script shall gracefully handle API rate limits, network errors, and invalid API responses.

FR4.2: The script shall report clear error messages when verification checks fail or are inconclusive.

6. Non-Functional Requirements
NFR1: Performance: The script should process references efficiently. API calls should be made asynchronously where possible to avoid blocking.

NFR2: Robustness: The script should be resilient to malformed input references and API failures.

NFR3: Maintainability: The code should be well-structured, modular, and extensively commented to allow for easy updates to formatting rules or API integrations.

NFR4: Scalability: The design should allow for future expansion to support more reference types or additional verification methods.

NFR5: Usability: The output should be clear, concise, and easy to interpret.

7. Technical Details and API Considerations
7.1 Programming Language
Python 3.x

7.2 Key Libraries/Modules
re (Regular Expressions): For parsing reference components and validating formats.

requests: For making HTTP requests to external APIs and URLs.

beautifulsoup4 (or similar): For parsing HTML content from websites (if content verification is implemented).

7.3 Potential Free APIs (Research Required for suitability and terms of use)
DOI Resolution:

CrossRef API: https://api.crossref.org/works/ - Excellent for resolving DOIs and getting metadata. Usually free for non-commercial use, check rate limits.

Website Accessibility:

Standard requests library in Python for HTTP GET requests. No specific API needed beyond that.

Academic Search/Journal Verification:

OpenAlex API: https://docs.openalex.org/ - A good alternative to Google Scholar for programmatic access to academic metadata. Free and comprehensive.

Semantic Scholar API: https://api.semanticscholar.org/ - Another option for academic paper metadata.

Book/ISBN Lookup:

Open Library Books API: https://openlibrary.org/developers/api - Good for ISBN lookup and book details.

Google Books API: Check free tier and usage policies.

General Web Search (for fallback):

This is the trickiest part as truly "free" and robust search APIs are rare. Options:

Serper.dev (Free tier): Offers a free tier for Google Search results.

Bing Web Search API (Azure Cognitive Services - Free tier): Requires Azure account, but has a free tier.

Custom Scraper (Last Resort): If no suitable API is found, a very basic, carefully designed scraper might be considered for public search engines, but this is prone to breakage and against terms of service for many sites. Prefer dedicated APIs.

8. High-Level Architecture
Input Reader: Reads references from file or string.

Reference Processor (Loop): Iterates through each reference.

Parser: Extracts components.

Formatter Validator: Checks CTR compliance.

Type Identifier: Determines reference type.

Verifier: Calls appropriate external APIs based on type and available components.

Output Formatter: Structures per-reference output.

Summary Generator: Aggregates results and generates final summary.

9. Development Considerations
Regular Expressions: Developing robust regex patterns for various Harvard CTR formats will be a significant part of the development effort.

API Key Management: While many suggested APIs have free tiers, some might require API keys. The script should be designed to easily incorporate these (e.g., via environment variables).

Rate Limiting: Implement delays or back-off strategies for API calls to respect rate limits.

User Agent: Use a descriptive User-Agent header for HTTP requests to APIs.

Testing: Thorough testing with a diverse set of valid, invalid, existing, and non-existing Harvard references is crucial.

This specification provides a comprehensive guide for implementing the Harvard Reference Validator and Verifier script.