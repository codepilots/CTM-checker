"""
Harvard Reference Validator and Verifier
Implements the specification in spec.md
"""
import re
import requests
import sys
from typing import List, Dict, Any, Optional

# Optional: For HTML parsing
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# Set stdout encoding to UTF-8 on Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- Input Reader ---
def read_references_from_file(filepath: str) -> List[str]:
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def read_references_from_string(refs: str) -> List[str]:
    return [line.strip() for line in refs.strip().split('\n') if line.strip()]

# --- Reference Parser & Type Identifier ---
def parse_reference(ref: str) -> Dict[str, Any]:
    # Improved regexes for Harvard CTR types and fallback detection
    patterns = {
        # Multiple authors: "Smith, J. and Doe, A." or "Smith, J., Doe, A. and Lee, B."
        'journal': re.compile(
            r"^(?P<author>(?:[A-Z][a-zA-Z\-']+, [A-Z](?:\.[A-Z]\.)?(?:, )?)+(?: and [A-Z][a-zA-Z\-']+, [A-Z](?:\.[A-Z]\.)?)?,?)\s*"
            r"\((?P<year>\d{4})\) ?'(?P<title>.+?)', ?(?P<journal>.+?), ?(?P<volume>\d+)\((?P<issue>\d+)\), ?pp\. ?(?P<pages>\d+-\d+)(\. doi:(?P<doi>\S+))?\."
        ),
        'journal_no_doi': re.compile(
            r"^(?P<author>(?:[A-Z][a-zA-Z\-']+, [A-Z](?:\.[A-Z]\.)?(?:, )?)+(?: and [A-Z][a-zA-Z\-']+, [A-Z](?:\.[A-Z]\.)?)?,?)\s*"
            r"\((?P<year>\d{4})\) '(?P<title>.+?)', (?P<journal>.+?), (?P<volume>\d+)\((?P<issue>\d+)\), pp\. (?P<pages>\d+-\d+)\.?$"
        ),
        'book': re.compile(
            r"^(?P<author>(?:[A-Z][a-zA-Z\-']+, (?:[A-Z]\.)+, )+(?:and (?:[A-Z][a-zA-Z\-']+, (?:[A-Z]\.)+,?))?) ?\((?P<year>\d{4})\) "
            r"(?P<title>.+?)\. (?P<location>.+?): (?P<publisher>.+?)(\. ISBN (?P<isbn>\S+))?\.?$"
        ),
        'website': re.compile(
            r"^(?P<author>(?:[A-Z][a-zA-Z\-']+, [A-Z]\.(?:, )?)+(?: and [A-Z][a-zA-Z\-']+, [A-Z]\.)?) "
            r"\((?P<year>\d{4})\) (?P<title>.+?)\. Available at: (?P<url>https?://\S+) \(Accessed: (?P<accessed>.+?)\)\."
        )
    }
    for ref_type, pat in patterns.items():
        m = pat.match(ref)
        if m:
            data = m.groupdict()
            if ref_type == 'journal_no_doi':
                data['type'] = 'journal'
                data['doi'] = None
            else:
                data['type'] = ref_type.replace('_no_doi', '')
            return data
    # Fallback: unknown type
    return {'type': 'unknown', 'raw': ref}

# --- CTR Format Validator ---
def validate_ctr_format(parsed: Dict[str, Any]) -> Dict[str, Any]:
    valid = True
    reasons = []
    t = parsed.get('type')
    if t == 'journal':
        if not re.match(r"^[A-Z][a-zA-Z\-']+, [A-Z]\.", parsed.get('author', '')):
            valid = False
            reasons.append("Incorrect author format")
        if not re.match(r"^\d{4}$", parsed.get('year', '')):
            valid = False
            reasons.append("Incorrect year format")
        if not parsed.get('volume') or not parsed.get('issue'):
            valid = False
            reasons.append("Missing volume/issue format")
        if not parsed.get('pages') or not re.match(r"^\d+-\d+$", parsed.get('pages', '')):
            valid = False
            reasons.append("Page format incorrect, should be pp. 25-35 not pages 25-35")
        if 'doi' in parsed and parsed.get('doi') is None:
            reasons.append("No DOI found (not required, but preferred)")
    elif t == 'book':
        if not re.match(r"^[A-Z][a-zA-Z\-']+, [A-Z]\.?", parsed.get('author', '')):
            valid = False
            reasons.append("Incorrect author format"+parsed.get('author', ''))
        if not re.match(r"^\d{4}$", parsed.get('year', '')):
            valid = False
            reasons.append("Incorrect year format")
    elif t == 'website':
        if not re.match(r"^[A-Z][a-zA-Z\-']+, [A-Z]\.", parsed.get('author', '')):
            valid = False
            reasons.append("Incorrect author format")
        if not re.match(r"^\d{4}$", parsed.get('year', '')):
            valid = False
            reasons.append("Incorrect year format")
        # Accessed date format: '15 July 2025'
        if not re.match(r"^\d{1,2} [A-Za-z]+ \d{4}$", parsed.get('accessed', '')):
            valid = False
            reasons.append("Accessed date format incorrect, should be '15 July 2025' not '{}'".format(parsed.get('accessed', '')))
    elif t == 'unknown':
        valid = False
        reasons.append("Could not identify reference type")
    return {'valid': valid, 'reasons': reasons}


# --- Source Verifier ---
def verify_source(parsed: Dict[str, Any], debug: bool = False) -> Dict[str, Any]:
    checks = []
    details = []
    clickable_link = "No direct link found."
    verified = "No"
    t = parsed.get('type')# Journal Article with DOI
    if t == 'journal' and parsed.get('doi'):
        checks.append("Identified reference type: Journal Article.")
        checks.append(f"Extracted DOI: {parsed['doi']}.")
        checks.append("Resolved DOI using CrossRef API.")
        url = f"https://api.crossref.org/works/{parsed['doi']}"
        try:
            r = requests.get(url, headers={"User-Agent": "CTR-Validator/1.0"}, timeout=10)
            if r.status_code == 200:
                data = r.json().get('message', {})
                title = data.get('title', [''])[0]
                authors = ', '.join([f"{a.get('family', '')}, {a.get('given', '')[0]}." for a in data.get('author', []) if 'family' in a and 'given' in a])
                details.append(f"DOI resolved successfully to '{title}' by {authors}.")
                journal = data.get('container-title', [''])[0]
                volume = data.get('volume', '')
                issue = data.get('issue', '')
                pages = data.get('page', '')
                details.append(f"Journal: {journal}, Volume {volume}, Issue {issue}, Pages {pages}.")
                verified = "Yes"
                clickable_link = f"https://doi.org/{parsed['doi']}"
            else:
                details.append("DOI did not resolve to a valid document.")
        except requests.exceptions.RequestException as e:
            details.append(f"Error resolving DOI: {str(e)}")

    # Book verification
    elif t == 'book':
        checks.append("Identified reference type: Book.")
        isbn = parsed.get('isbn')
        if isbn:
            checks.append(f"Extracted ISBN: {isbn}.")
            checks.append("Verifying ISBN using OpenLibrary API.")
            # Try OpenLibrary ISBN API first
            url = f"https://openlibrary.org/isbn/{isbn}.json"
            if debug:
                details.append(f"DEBUG: OpenLibrary ISBN API URL: {url}")
            try:
                r = requests.get(url, headers={"User-Agent": "CTR-Validator/1.0"}, timeout=10)
                if debug:
                    details.append(f"DEBUG: OpenLibrary API response status: {r.status_code}")
                    # dump out headers for debugging
                    details.append(f"DEBUG: OpenLibrary API response headers: {r.headers}")
                    # dump out the first 100 characters of the response body
                    details.append(f"DEBUG: OpenLibrary API response body (first 100 chars): {r.text[:100]}")

                # handle a redirect 
                if r.status_code == 301 or r.status_code == 302:
                    redirect_url = r.headers.get('Location')
                    if redirect_url:
                        details.append(f"DEBUG: Redirected to {redirect_url}")
                        r = requests.get(redirect_url, headers={"User-Agent": "CTR-Validator/1.0"}, timeout=10)
                        if debug:
                            details.append(f"DEBUG: Redirected API response status: {r.status_code}")

                if r.status_code == 200:
                    data = r.json()
                    #isbn_key = f"ISBN:{isbn}"
                    #if isbn_key in data:
                    book_data = data
                    title = book_data.get('title', 'Unknown title')
                    authors = book_data.get('authors', [])
                    #author_names = [author.get('name', 'Unknown') for author in authors]
                    publishers = book_data.get('publishers', [])
                    #publisher_names = [pub.get('name', 'Unknown') for pub in publishers]
                    pub_date = book_data.get('publish_date', 'Unknown')
                    
                    if debug:
                        details.append(f"DEBUG: Found book data: Title='{title}', Authors={authors}, Publishers={publishers}, Date={pub_date}")
                    
                    details.append(f"ISBN verified: '{title}' by {authors}.")
                    details.append(f"Publisher: {publishers}, Published: {pub_date}.")
                    verified = "Yes"
                    clickable_link = f"https://openlibrary.org/isbn/{isbn}"
                    #else:
                    #    details.append("ISBN not found in OpenLibrary database.")
                    #    if debug:
                    #        details.append(f"DEBUG: No data found for ISBN key '{isbn_key}' in response")
                else:
                    details.append("Error accessing OpenLibrary ISBN database.")
                    if debug:
                        details.append(f"DEBUG: OpenLibrary API returned status {r.status_code}")
            except requests.exceptions.RequestException as e:
                details.append(f"Error verifying ISBN: {str(e)}")
                if debug:
                    details.append(f"DEBUG: ISBN verification exception: {type(e).__name__}: {str(e)}")
        
        # Fallback search for books without ISBN or failed ISBN lookup
        if verified == "No":
            checks.append("Performing general book search.")
            query = f"{parsed.get('title', '')} {parsed.get('author', '')} {parsed.get('publisher', '')}"
            url = f"https://openlibrary.org/search.json?q={requests.utils.quote(query)}&limit=5"
            if debug:
                details.append(f"DEBUG: Book search query: '{query}'")
                details.append(f"DEBUG: OpenLibrary search URL: {url}")
            try:
                r = requests.get(url, headers={"User-Agent": "CTR-Validator/1.0"}, timeout=10)
                if debug:
                    details.append(f"DEBUG: Search API response status: {r.status_code}")
                if r.status_code == 200:
                    data = r.json()
                    num_found = data.get('numFound', 0)
                    if debug:
                        details.append(f"DEBUG: Total search results: {num_found}")
                    
                    if num_found > 0:
                        docs = data.get('docs', [])
                        if debug:
                            details.append(f"DEBUG: Number of results returned: {len(docs)}")
                            
                            # Show details of first few results
                            for i, doc in enumerate(docs[:3]):
                                title = doc.get('title', 'No title')
                                authors = doc.get('author_name', ['Unknown author'])
                                first_pub_year = doc.get('first_publish_year', 'Unknown')
                                publishers = doc.get('publisher', ['Unknown publisher'])
                                isbn_list = doc.get('isbn', [])
                                
                                details.append(f"DEBUG: Book result {i+1}: Title='{title}'")
                                details.append(f"DEBUG: Book result {i+1}: Authors={authors[:2]}")
                                details.append(f"DEBUG: Book result {i+1}: First published={first_pub_year}")
                                details.append(f"DEBUG: Book result {i+1}: Publishers={publishers[:2]}")
                                details.append(f"DEBUG: Book result {i+1}: ISBNs={isbn_list[:2] if isbn_list else 'None'}")
                        
                        # check if any result matches the parsed reference
                        for i, doc in enumerate(docs):
                            if (doc.get('title', '').lower() == parsed.get('title', '').lower() and
                                any(author.lower() in parsed.get('author', '').lower() for author in doc.get('author_name', []))):
                                details.append(f"DEBUG: Found matching book for reference {i+1}: {doc.get('title', '')}")
                                verified = "Yes"
                                break
                        
                        if verified == "No":
                            details.append("General book search found potential matches, but no definitive match.")
                            if docs:
                                first_doc = docs[0]
                                title = first_doc.get('title', 'No title')
                                authors = first_doc.get('author_name', ['Unknown author'])
                                first_pub_year = first_doc.get('first_publish_year', 'Unknown')
                                publishers = first_doc.get('publisher', ['Unknown publisher'])
                                isbn_list = first_doc.get('isbn', [])
                                
                                details.append(f"First match: Title='{title}', Authors={authors[:2]}, Year={first_pub_year}, Publishers={publishers[:2]}, ISBNs={isbn_list[:2] if isbn_list else 'None'}.")
                                verified = "Partial"
                    else:
                        details.append("General book search did not find any matches.")
                else:
                    if debug:
                        details.append(f"DEBUG: Book search API failed with status {r.status_code}")
                    details.append("Error performing book search.")
            except requests.exceptions.RequestException as e:
                details.append(f"Error performing book search: {str(e)}")
                if debug:
                    details.append(f"DEBUG: Book search exception: {type(e).__name__}: {str(e)}")
            
    # Fallback for failed DOI resolution
    if verified == "No" and t == 'journal':
        checks.append("Performed general academic search for article.")
        query = f"{parsed.get('title', '')}"# {parsed.get('author', '')} {parsed.get('journal', '')}"
        url = f"https://api.openalex.org/works?search={requests.utils.quote(query)}"
        if debug:
            details.append(f"DEBUG: Fallback search query: '{query}'")
            details.append(f"DEBUG: OpenAlex API URL: {url}")
        try:
            r = requests.get(url, headers={"User-Agent": "CTR-Validator/1.0"}, timeout=10)
            if debug:
                details.append(f"DEBUG: API response status: {r.status_code}")
            if r.status_code == 200:
                json_data = r.json()
                meta = json_data.get('meta', {})
                count = meta.get('count', 0)
                if debug:
                    details.append(f"DEBUG: Total search results count: {count}")
                
                if count > 0:
                    results = json_data.get('results', [])
                    if debug:
                        details.append(f"DEBUG: Number of results returned: {len(results)}")
                        
                        # Show details of first few results
                        for i, result in enumerate(results[:3]):  # Show first 3 results
                            title = result.get('title', 'No title')
                            authors = result.get('authorships', [])
                            author_names = [auth.get('author', {}).get('display_name', 'Unknown') for auth in authors[:2]]  # First 2 authors
                            journal_name = ''
                            if result.get('primary_location'):
                                journal_name = result.get('primary_location', {}).get('source', {}).get('display_name', 'Unknown journal')
                            pub_year = result.get('publication_year', 'Unknown')
                            doi = result.get('doi', 'No DOI')
                            
                            details.append(f"DEBUG: Result {i+1}: Title='{title}'")
                            details.append(f"DEBUG: Result {i+1}: Authors={', '.join(author_names)}")
                            details.append(f"DEBUG: Result {i+1}: Journal='{journal_name}'")
                            details.append(f"DEBUG: Result {i+1}: Year={pub_year}")
                            details.append(f"DEBUG: Result {i+1}: DOI={doi}")
                    
                    for i, result in enumerate(results):
                        if parsed.get('title', '').lower() in result.get('title', '').lower() and parsed.get('author', '').split(',')[0] in result.get('authorships', [{}])[0].get('author', {}).get('display_name', '') and str(parsed.get('year', '')) == str(result.get('publication_year', '')):
                            verified = "Yes"
                            clickable_link = result.get('doi', 'No DOI')
                            details.append(f"Verified match found: Title='{result.get('title', '')}', DOI='{clickable_link}'.")
                            if clickable_link.startswith("http"):
                                parsed['doi'] = clickable_link.split("doi.org/")[-1]
                            break

                    if verified == "No":
                        details.append("General academic search found potential matches, but no definitive match.")
                        if count > 0:
                            first_result = results[0]
                            title = first_result.get('title', 'No title')
                            authors = first_result.get('authorships', [])
                            author_names = ', '.join([auth.get('author', {}).get('display_name', 'Unknown') for auth in authors])
                            journal_name = first_result.get('primary_location', {}).get('source', {}).get('display_name', 'Unknown journal')
                            pub_year = first_result.get('publication_year', 'Unknown')
                            doi = first_result.get('doi', 'No DOI')
                            details.append(f"First match: Title='{title}', Authors='{author_names}', Year={pub_year}, Journal='{journal_name}', DOI='{doi}'.")
                        verified = "Partial"
                else:
                    details.append("General academic search did not find a match.") #else:
                if debug:
                    details.append(f"DEBUG: API request failed with status {r.status_code}")
                # Fetch abstract if DOI is available
                if parsed.get('doi'):
                    abstract_url = f"https://api.crossref.org/works/{parsed['doi']}"
                    try:
                        abstract_response = requests.get(abstract_url, headers={"User-Agent": "CTR-Validator/1.0"}, timeout=10)
                        if abstract_response.status_code == 200:
                            abstract_data = abstract_response.json().get('message', {})
                            abstract = abstract_data.get('abstract', None)
                            if abstract:
                                details.append(f"Abstract: {abstract}")
                            else:
                                details.append("Abstract not available for this DOI.")
                        else:
                            details.append("Failed to fetch abstract from DOI.")
                    except requests.exceptions.RequestException as e:
                        details.append(f"Error fetching abstract: {str(e)}")
        except requests.exceptions.RequestException as e:
            details.append(f"Error performing academic search: {str(e)}")
            if debug:
                details.append(f"DEBUG: Exception details: {type(e).__name__}: {str(e)}")



    # Return verification results
    return {
        'checks': checks,
        'details': details,
        'clickable_link': clickable_link,
        'verified': verified
    }

# --- Output Formatter ---
def format_reference_output(ref: str, parsed: Dict[str, Any], ctr_result: Dict[str, Any], ver_result: Dict[str, Any], idx: int) -> str:
    out = [f"--- Reference {idx+1} ---"]
    out.append(f"Original Reference: {ref}")
    out.append(f"CTR Format Valid: {'Yes' if ctr_result['valid'] else 'No'}" + (f" (Reason: {', '.join(ctr_result['reasons'])})" if not ctr_result['valid'] else ""))
    out.append(f"Source Verified: {ver_result['verified']}")
    out.append("Checks Performed:")
    for c in ver_result['checks']:
        out.append(f"  - {c}")
    out.append("Verification Details:")
    for d in ver_result['details']:
        out.append(f"  - {d}")
    out.append(f"Clickable Link: {ver_result['clickable_link']}")
    return '\n'.join(out)

# --- Summary Generator ---
def format_summary(total: int, valid_ctr: int, verified: int) -> str:
    return f"""
--- Summary ---
Total references checked: {total}
References with valid CTR format: {valid_ctr}
References verified correct: {verified}
"""# --- Main Entrypoint ---
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Harvard Reference Validator and Verifier")
    parser.add_argument('-f', '--file', help='Path to reference list file')
    parser.add_argument('-s', '--string', help='Direct string input of references (\n separated)')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output for DOI resolution fallback')
    args = parser.parse_args()
    if args.file:
        refs = read_references_from_file(args.file)
    elif args.string:
        refs = read_references_from_string(args.string)
    else:
        print("No input provided. Use -f <file> or -s <string>.")
        return
    outputs = []
    valid_ctr = 0
    verified = 0
    for idx, ref in enumerate(refs):
        parsed = parse_reference(ref)
        ctr_result = validate_ctr_format(parsed)
        if ctr_result['valid']:
            valid_ctr += 1
        ver_result = verify_source(parsed, debug=args.debug)
        if ver_result['verified'] == 'Yes':
            verified += 1
        outputs.append(format_reference_output(ref, parsed, ctr_result, ver_result, idx))
    print('\n\n'.join(outputs))
    print(format_summary(len(refs), valid_ctr, verified))

if __name__ == '__main__':
    main()
