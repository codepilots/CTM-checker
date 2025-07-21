import re
import json
import io
import sys
import subprocess
import tempfile
import os

# The test references from the Canvas
TEST_REFERENCES = """
Browne, T.B., Carlson, T.B. and Hastie, P.A., (2004) 'A comparison of rugby seasons presented in traditional and sport education formats', European Physical Education Review, 10(2), pp.199-214.
"""
#Palmer, P. (2007) 'The social effects of sport: What rugby can teach us', Journal of Sports Sociology, 15(3), pp. 210-225.
#Smith, J. and Jones, A. (2020) 'The impact of digital technology on education', Educational Technology & Society, 23(1), pp. 123-135. doi: 10.1109/SET.2020.1234567.
#Davies, C. (2023) 'The future of artificial intelligence', New Scientist, 257(3429), pp. 30-35.
#Johnson, R. (2024) 'UK economy shows signs of recovery', The Guardian, 15 May. Available at: www.theguardian.com/business/uk-economy-recovery (Accessed: 18 July 2025).
#NHS (2023) Understanding mental health conditions. Available at: www.nhs.uk/mental-health/conditions/ (Accessed: 18 July 2025).
#"""
# Smith, J. (2020) 'The Future of AI', Journal of Advanced Robotics, 15(2), pp. 123-145. doi:10.1000/j.ar.2020.02.001
# Jones, A. (2019) Understanding Climate Change. London: Green Press.
# Brown, C. (2021) Digital Transformation. Available at: https://www.example.com/digital-transformation-report (Accessed: 15 July 2025).
# Davis, M. (2018) 'Quantum Computing Advances', Physics Review, 3(1), pp. 50-65.
# Miller, S. (2022) Sustainable Energy Solutions. New York: Eco Publishers.
# White, E. (2023) 'The Impact of Social Media', Online Journal of Communication, 10(4), pp. 200-215. doi:10.1000/ojc.2023.04.001
# Taylor, R. (2017) Data Science Handbook. Boston: Tech Books.
# Green, L. (2016) 'Blockchain Technology', Financial Times, 2016, Available at: https://www.ft.com/blockchain-tech (Accessed: 10 January 2024).
# Hall, P. (2015) Artificial Intelligence: A Modern Approach. Cambridge, MA: MIT Press.
# King, D. (2024) 'Cybersecurity Threats', Journal of Digital Security, 8(3), pp. 78-92.
# Lewis, F. (2020) 'Renewable Energy Policy', Energy Policy Review, 12(1). pp. 30-45. (Missing volume/issue format)
# Wright, G. (2019) 'The History of the Internet', Tech Review. Available at: https://www.nonexistent-site.com/internet-history (Accessed: 22 February 2023). (Non-existent URL)
# Young, H. (2021) 'Machine Learning Algorithms', Journal of AI Research, 7(2), pp. 110-125. doi:10.1000/j.air.2021.02.005
# Clark, K. (2018) 'Big Data Analytics', International Journal of Data Science, 5(3), pp. 150-165.
# Baker, N. (2023) Future of Work. London: Business Press.
# Adams, O. (2017) 'Cloud Computing', IEEE Transactions on Computers, 66(11), pp. 1890-1900. doi:10.1109/TC.2017.2750000
# Carter, Q. (2020) 'Virtual Reality in Education', Educational Technology Journal, 4(1), pages 25-35. (Incorrect page format)
# Evans, V. (2016) Global Warming: A Concise Guide. New York: Earth Books.
# Fisher, W. (2022) 'The Ethics of AI', AI and Society, 37(2), pp. 300-315.
# Gordon, X. (2019) 'Space Exploration', Astrophysical Journal, 876(1), pp. 1-10. doi:10.3847/1538-4357/ab1234
# Harris, Y. (2021) 'The Psychology of Decision Making', Behavioral Science Review, 1(1), pp. 1-15.
# Ingram, Z. (2018) 'Cybersecurity Best Practices', Security Today. Available at: https://www.securitytoday.com/best-practices (Accessed: 01 March 2024).
# Jackson, A. (2020) 'The Rise of E-commerce', Journal of Business Studies, 10(2), pp. 80-95.
# Kelly, B. (2017) Quantum Physics for Beginners. Princeton: University Press.
# Lee, C. (2023) 'The Future of Renewable Energy', Environmental Science & Technology, 57(10), pp. 3800-3810. doi:10.1021/acs.est.2c07000
# Morgan, D. (2019) 'The Economic Impact of Pandemics', Health Economics Review, 6(3), pp. 112-125.
# Nelson, E. (2021) 'The Role of Big Data in Healthcare', Health Informatics Journal, 27(4), pp. 290-305.
# Owens, G. (2016) 'The History of Photography', Art History Quarterly, 5(2), pp. 70-85.
# Parker, H. (2022) 'Sustainable Agriculture', Journal of Agricultural Science, 17(1), pp. 40-55.
# Quinn, I. (2019) 'The Evolution of Programming Languages', Software Engineering Journal, 12(4), pp. 200-215.
# Roberts, J. (2020) 'The Ethics of Genetic Engineering', Bioethics Review, 8(1), pp. 10-25.
# Scott, K. (2017) 'The Impact of Climate Change on Biodiversity', Conservation Biology, 31(5), pp. 1000-1015. doi:10.1111/cobi.12900
# Turner, L. (2023) 'The Future of Space Travel', Space Exploration Today, Vol. 1, No. 1, pp. 1-10. (Incorrect volume/issue format)
# Upton, M. (2018) 'Artificial Intelligence in Medicine', Medical AI Journal, 2(2), pp. 50-60.
# Vance, N. (2021) 'The Psychology of Online Behavior', Cyberpsychology: Journal of Psychosocial Research on Cyberspace, 15(1), pp. 1-15.
# Wagner, O. (2019) 'The History of Robotics', Robotics Today. Available at: http://www.robotics-history.org/ (Accessed: 2024-05-01). (Incorrect access date format)
# Xylos, P. (2020) 'Quantum Entanglement', Physical Review Letters, 125(10), pp. 100401. doi:10.1103/PhysRevLett.125.100401
# Yu, Q. (2017) 'The Neuroscience of Learning', Brain & Cognition, 118, pp. 100-110.
# Zander, R. (2022) 'The Impact of Renewable Energy on Grid Stability', Energy Systems Journal, 9(3), pp. 180-195.
# Abbott, S. (2015) 'The Internet of Things', Communications of the ACM, 58(11), pp. 62-70. doi:10.1145/2810287 (Non-existent DOI)
# """

def parse_validator_output(output_string):
    """
    Parses the output string from the Harvard validator script into a structured
    Python dictionary for easier comparison.
    """
    parsed_data = {"references": [], "summary": {}}
    current_ref = {}
    current_section = None
    ref_count = 0

    lines = output_string.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("--- Reference"):
            if current_ref: # Save previous reference if exists
                parsed_data["references"].append(current_ref)
            ref_count += 1
            current_ref = {"Original Reference": "", "CTR Format Valid": "", "Source Verified": "",
                           "Checks Performed": [], "Verification Details": [], "Clickable Link": ""}
            current_section = None # Reset section
        elif line.startswith("--- Summary ---"):
            if current_ref:
                parsed_data["references"].append(current_ref)
            current_section = "summary"
        elif current_section == "summary":
            if ":" in line:
                key, value = line.split(":", 1)
                parsed_data["summary"][key.strip()] = value.strip()
        elif line.startswith("Original Reference:"):
            current_ref["Original Reference"] = line.split(":", 1)[1].strip()
        elif line.startswith("CTR Format Valid:"):
            current_ref["CTR Format Valid"] = line.split(":", 1)[1].strip()
        elif line.startswith("Source Verified:"):
            current_ref["Source Verified"] = line.split(":", 1)[1].strip()
        elif line.startswith("Checks Performed:"):
            current_section = "checks"
            current_ref["Checks Performed"] = []
        elif line.startswith("Verification Details:"):
            current_section = "details"
            current_ref["Verification Details"] = []
        elif line.startswith("Clickable Link:"):
            current_ref["Clickable Link"] = line.split(":", 1)[1].strip()
            current_section = None # End of reference block
        elif current_section == "checks" and line.startswith("-"):
            current_ref["Checks Performed"].append(line[1:].strip())
        elif current_section == "details" and line.startswith("-"):
            current_ref["Verification Details"].append(line[1:].strip())

    return parsed_data

def run_test():
    """
    Runs the test by calling the external 'ctr_validator.py' script
    and comparing its output to the expected structure.
    """
    print("--- Starting Harvard Reference Validator Test ---")

    # Create a temporary file to pass references to the script
    temp_file = None
    temp_file_path = None # Initialize to None for finally block
    try:
        # Use NamedTemporaryFile to get a file path that can be passed to subprocess
        # delete=False ensures the file is not deleted immediately after closing,
        # allowing subprocess to access it. We'll delete it manually in finally block.
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(TEST_REFERENCES)
            temp_file_path = temp_file.name

        print(f"References written to temporary file: {temp_file_path}")
        print(f"Attempting to call 'ctr_validator.py' with input file...")

        # 1. Call the external 'ctr_validator.py' script
        # Ensure 'ctr_validator.py' is in the same directory or in your PATH
        # The script is expected to take the file path as a command-line argument
        result = subprocess.run(
            ['python', 'ctr_validator.py','-f', temp_file_path],
            capture_output=True,
            text=True, # Capture stdout/stderr as text, not bytes
            check=False, # Do NOT raise CalledProcessError immediately, capture stderr first
            encoding='utf-8' # Ensure output is decoded as UTF-8
        )

        print(f"Subprocess call completed with exit code: {result.returncode}")

        if result.stdout:
            actual_output_string = result.stdout
            print("\n--- Actual Output from ctr_validator.py (STDOUT) ---")
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass
            try:
                print(actual_output_string)
            except Exception as e:
                print(actual_output_string.encode('utf-8', errors='replace').decode('utf-8'))
            print("---------------------------------------------------\n")
        else:
            actual_output_string = ""
            print("\n--- ctr_validator.py produced NO STDOUT. ---")

        if result.stderr:
            print("\n--- Actual Errors from ctr_validator.py (STDERR) ---")
            print(result.stderr)
            print("---------------------------------------------------\n")
        else:
            print("\n--- ctr_validator.py produced NO STDERR. ---")

        # If the script exited with an error, report it
        if result.returncode != 0:
            print(f"FAIL: The 'ctr_validator.py' script exited with a non-zero status code: {result.returncode}")
            if not result.stderr:
                print("  (No specific error message was printed to STDERR by ctr_validator.py)")
            return # Exit the test function early

        # 2. Parse the actual output
        print("Attempting to parse the captured output...")
        actual_parsed_data = parse_validator_output(actual_output_string)
        print("Output parsing complete.")

        # 3. Define expected parsed data (based on manual analysis of TEST_REFERENCES
        #    and the software specification's output examples)
        expected_parsed_data = {
            "references": [
                {
                    "Original Reference": "Smith, J. (2020) 'The Future of AI', Journal of Advanced Robotics, 15(2), pp. 123-145. doi:10.1000/j.ar.2020.02.001",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Yes",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Extracted DOI: 10.1000/j.ar.2020.02.001.", "Resolved DOI using CrossRef API."],
                    "Verification Details": ["DOI resolved successfully to 'The Future of AI' by J. Smith.", "Journal: Journal of Advanced Robotics, Volume 15, Issue 2, Pages 123-145."],
                    "Clickable Link": "https://doi.org/10.1000/j.ar.2020.02.001"
                },
                {
                    "Original Reference": "Jones, A. (2019) Understanding Climate Change. London: Green Press.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Book.", "Attempted ISBN lookup (no ISBN found in reference).", "Performed general web search for 'Understanding Climate Change'."],
                    "Verification Details": ["No direct ISBN for lookup.", "General web search found multiple results, but no definitive, direct link to the specific edition."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Brown, C. (2021) Digital Transformation. Available at: https://www.example.com/digital-transformation-report (Accessed: 15 July 2025).",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Yes",
                    "Checks Performed": ["Identified reference type: Website.", "Checked URL accessibility.", "Verified presence of keywords on the page."],
                    "Verification Details": ["URL is accessible (HTTP 200 OK).", "Keywords 'Digital Transformation' found on the webpage."],
                    "Clickable Link": "https://www.example.com/digital-transformation-report"
                },
                {
                    "Original Reference": "Davis, M. (2018) 'Quantum Computing Advances', Physics Review, 3(1), pp. 50-65.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Miller, S. (2022) Sustainable Energy Solutions. New York: Eco Publishers.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Book.", "Attempted ISBN lookup (no ISBN found in reference).", "Performed general web search for 'Sustainable Energy Solutions'."],
                    "Verification Details": ["No direct ISBN for lookup.", "General web search found multiple results, but no definitive, direct link to the specific edition."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "White, E. (2023) 'The Impact of Social Media', Online Journal of Communication, 10(4), pp. 200-215. doi:10.1000/ojc.2023.04.001",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Yes",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Extracted DOI: 10.1000/ojc.2023.04.001.", "Resolved DOI using CrossRef API."],
                    "Verification Details": ["DOI resolved successfully to 'The Impact of Social Media' by E. White.", "Journal: Online Journal of Communication, Volume 10, Issue 4, Pages 200-215."],
                    "Clickable Link": "https://doi.org/10.1000/ojc.2023.04.001"
                },
                {
                    "Original Reference": "Taylor, R. (2017) Data Science Handbook. Boston: Tech Books.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Book.", "Attempted ISBN lookup (no ISBN found in reference).", "Performed general web search for 'Data Science Handbook'."],
                    "Verification Details": ["No direct ISBN for lookup.", "General web search found multiple results, but no definitive, direct link to the specific edition."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Green, L. (2016) 'Blockchain Technology', Financial Times, 2016, Available at: https://www.ft.com/blockchain-tech (Accessed: 10 January 2024).",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Yes",
                    "Checks Performed": ["Identified reference type: Website.", "Checked URL accessibility.", "Verified presence of keywords on the page."],
                    "Verification Details": ["URL is accessible (HTTP 200 OK).", "Keywords 'Blockchain Technology' found on the webpage."],
                    "Clickable Link": "https://www.ft.com/blockchain-tech"
                },
                {
                    "Original Reference": "Hall, P. (2015) Artificial Intelligence: A Modern Approach. Cambridge, MA: MIT Press.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Book.", "Attempted ISBN lookup (no ISBN found in reference).", "Performed general web search for 'Artificial Intelligence: A Modern Approach'."],
                    "Verification Details": ["No direct ISBN for lookup.", "General web search found multiple results, but no definitive, direct link to the specific edition."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "King, D. (2024) 'Cybersecurity Threats', Journal of Digital Security, 8(3), pp. 78-92.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Lewis, F. (2020) 'Renewable Energy Policy', Energy Policy Review, 12(1). pp. 30-45. (Missing volume/issue format)",
                    "CTR Format Valid": "No",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["Reason: 'Volume/issue format incorrect, should be 12(1), pp. 30-45 not 12(1). pp. 30-45'", "General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Wright, G. (2019) 'The History of the Internet', Tech Review. Available at: https://www.nonexistent-site.com/internet-history (Accessed: 22 February 2023). (Non-existent URL)",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "No",
                    "Checks Performed": ["Identified reference type: Website.", "Checked URL accessibility."],
                    "Verification Details": ["URL is not accessible (HTTP 404/Connection Error)."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Young, H. (2021) 'Machine Learning Algorithms', Journal of AI Research, 7(2), pp. 110-125. doi:10.1000/j.air.2021.02.005",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Yes",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Extracted DOI: 10.1000/j.air.2021.02.005.", "Resolved DOI using CrossRef API."],
                    "Verification Details": ["DOI resolved successfully to 'Machine Learning Algorithms' by H. Young.", "Journal: Journal of AI Research, Volume 7, Issue 2, Pages 110-125."],
                    "Clickable Link": "https://doi.org/10.1000/j.air.2021.02.005"
                },
                {
                    "Original Reference": "Clark, K. (2018) 'Big Data Analytics', International Journal of Data Science, 5(3), pp. 150-165.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Baker, N. (2023) Future of Work. London: Business Press.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Book.", "Attempted ISBN lookup (no ISBN found in reference).", "Performed general web search for 'Future of Work'."],
                    "Verification Details": ["No direct ISBN for lookup.", "General web search found multiple results, but no definitive, direct link to the specific edition."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Adams, O. (2017) 'Cloud Computing', IEEE Transactions on Computers, 66(11), pp. 1890-1900. doi:10.1109/TC.2017.2750000",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Yes",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Extracted DOI: 10.1109/TC.2017.2750000.", "Resolved DOI using CrossRef API."],
                    "Verification Details": ["DOI resolved successfully to 'Cloud Computing' by O. Adams.", "Journal: IEEE Transactions on Computers, Volume 66, Issue 11, Pages 1890-1900."],
                    "Clickable Link": "https://doi.org/10.1109/TC.2017.2750000"
                },
                {
                    "Original Reference": "Carter, Q. (2020) 'Virtual Reality in Education', Educational Technology Journal, 4(1), pages 25-35. (Incorrect page format)",
                    "CTR Format Valid": "No",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["Reason: 'Page format incorrect, should be pp. 25-35 not pages 25-35'", "General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Evans, V. (2016) Global Warming: A Concise Guide. New York: Earth Books.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Book.", "Attempted ISBN lookup (no ISBN found in reference).", "Performed general web search for 'Global Warming: A Concise Guide'."],
                    "Verification Details": ["No direct ISBN for lookup.", "General web search found multiple results, but no definitive, direct link to the specific edition."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Fisher, W. (2022) 'The Ethics of AI', AI and Society, 37(2), pp. 300-315.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Gordon, X. (2019) 'Space Exploration', Astrophysical Journal, 876(1), pp. 1-10. doi:10.3847/1538-4357/ab1234",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Yes",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Extracted DOI: 10.3847/1538-4357/ab1234.", "Resolved DOI using CrossRef API."],
                    "Verification Details": ["DOI resolved successfully to 'Space Exploration' by X. Gordon.", "Journal: Astrophysical Journal, Volume 876, Issue 1, Pages 1-10."],
                    "Clickable Link": "https://doi.org/10.3847/1538-4357/ab1234"
                },
                {
                    "Original Reference": "Harris, Y. (2021) 'The Psychology of Decision Making', Behavioral Science Review, 1(1), pp. 1-15.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Ingram, Z. (2018) 'Cybersecurity Best Practices', Security Today. Available at: https://www.securitytoday.com/best-practices (Accessed: 01 March 2024).",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Yes",
                    "Checks Performed": ["Identified reference type: Website.", "Checked URL accessibility.", "Verified presence of keywords on the page."],
                    "Verification Details": ["URL is accessible (HTTP 200 OK).", "Keywords 'Cybersecurity Best Practices' found on the webpage."],
                    "Clickable Link": "https://www.securitytoday.com/best-practices"
                },
                {
                    "Original Reference": "Jackson, A. (2020) 'The Rise of E-commerce', Journal of Business Studies, 10(2), pp. 80-95.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Kelly, B. (2017) Quantum Physics for Beginners. Princeton: University Press.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Book.", "Attempted ISBN lookup (no ISBN found in reference).", "Performed general web search for 'Quantum Physics for Beginners'."],
                    "Verification Details": ["No direct ISBN for lookup.", "General web search found multiple results, but no definitive, direct link to the specific edition."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Lee, C. (2023) 'The Future of Renewable Energy', Environmental Science & Technology, 57(10), pp. 3800-3810. doi:10.1021/acs.est.2c07000",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Yes",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Extracted DOI: 10.1021/acs.est.2c07000.", "Resolved DOI using CrossRef API."],
                    "Verification Details": ["DOI resolved successfully to 'The Future of Renewable Energy' by C. Lee.", "Journal: Environmental Science & Technology, Volume 57, Issue 10, Pages 3800-3810."],
                    "Clickable Link": "https://doi.org/10.1021/acs.est.2c07000"
                },
                {
                    "Original Reference": "Morgan, D. (2019) 'The Economic Impact of Pandemics', Health Economics Review, 6(3), pp. 112-125.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Nelson, E. (2021) 'The Role of Big Data in Healthcare', Health Informatics Journal, 27(4), pp. 290-305.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Owens, G. (2016) 'The History of Photography', Art History Quarterly, 5(2), pp. 70-85.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Parker, H. (2022) 'Sustainable Agriculture', Journal of Agricultural Science, 17(1), pp. 40-55.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Quinn, I. (2019) 'The Evolution of Programming Languages', Software Engineering Journal, 12(4), pp. 200-215.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Roberts, J. (2020) 'The Ethics of Genetic Engineering', Bioethics Review, 8(1), pp. 10-25.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Scott, K. (2017) 'The Impact of Climate Change on Biodiversity', Conservation Biology, 31(5), pp. 1000-1015. doi:10.1111/cobi.12900",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Yes",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Extracted DOI: 10.1111/cobi.12900.", "Resolved DOI using CrossRef API."],
                    "Verification Details": ["DOI resolved successfully to 'The Impact of Climate Change on Biodiversity' by K. Scott.", "Journal: Conservation Biology, Volume 31, Issue 5, Pages 1000-1015."],
                    "Clickable Link": "https://doi.org/10.1111/cobi.12900"
                },
                {
                    "Original Reference": "Turner, L. (2023) 'The Future of Space Travel', Space Exploration Today, Vol. 1, No. 1, pp. 1-10. (Incorrect volume/issue format)",
                    "CTR Format Valid": "No",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["Reason: 'Volume/issue format incorrect, should be 1(1), pp. 1-10 not Vol. 1, No. 1'", "General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Upton, M. (2018) 'Artificial Intelligence in Medicine', Medical AI Journal, 2(2), pp. 50-60.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Vance, N. (2021) 'The Psychology of Online Behavior', Cyberpsychology: Journal of Psychosocial Research on Cyberspace, 15(1), pp. 1-15.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Wagner, O. (2019) 'The History of Robotics', Robotics Today. Available at: http://www.robotics-history.org/ (Accessed: 2024-05-01). (Incorrect access date format)",
                    "CTR Format Valid": "No",
                    "Source Verified": "Yes", # URL is reachable, even if format is wrong
                    "Checks Performed": ["Identified reference type: Website.", "Checked URL accessibility.", "Verified presence of keywords on the page."],
                    "Verification Details": ["Reason: 'Accessed date format incorrect, should be '1 May 2024' not '2024-05-01''", "URL is accessible (HTTP 200 OK).", "Keywords 'History of Robotics' found on the webpage."],
                    "Clickable Link": "http://www.robotics-history.org/"
                },
                {
                    "Original Reference": "Xylos, P. (2020) 'Quantum Entanglement', Physical Review Letters, 125(10), pp. 100401. doi:10.1103/PhysRevLett.125.100401",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Yes",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Extracted DOI: 10.1103/PhysRevLett.125.100401.", "Resolved DOI using CrossRef API."],
                    "Verification Details": ["DOI resolved successfully to 'Quantum Entanglement' by P. Xylos.", "Journal: Physical Review Letters, Volume 125, Issue 10, Pages 100401."],
                    "Clickable Link": "https://doi.org/10.1103/PhysRevLett.125.100401"
                },
                {
                    "Original Reference": "Yu, Q. (2017) 'The Neuroscience of Learning', Brain & Cognition, 118, pp. 100-110.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Zander, R. (2022) 'The Impact of Renewable Energy on Grid Stability', Energy Systems Journal, 9(3), pp. 180-195.",
                    "CTR Format Valid": "Yes",
                    "Source Verified": "Partial",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Performed general academic search for article."],
                    "Verification Details": ["General academic search found potential matches, but no definitive, direct link."],
                    "Clickable Link": "No direct link found."
                },
                {
                    "Original Reference": "Abbott, S. (2015) 'The Internet of Things', Communications of the ACM, 58(11), pp. 62-70. doi:10.1145/2810287 (Non-existent DOI)",
                    "CTR Format Valid": "Yes", # Format is correct, only DOI is non-existent
                    "Source Verified": "No",
                    "Checks Performed": ["Identified reference type: Journal Article.", "Extracted DOI: 10.1145/2810287.", "Resolved DOI using CrossRef API."],
                    "Verification Details": ["DOI did not resolve to a valid document."],
                    "Clickable Link": "No direct link found."
                }
            ],
            "summary": {
                "Total references checked": "40",
                "References with valid CTR format": "36",
                "References verified correct": "11"
            }
        }

        # 4. Compare actual and expected parsed data
        test_passed = True

        # Compare references
        if len(actual_parsed_data["references"]) != len(expected_parsed_data["references"]):
            print(f"FAIL: Mismatched number of references. Expected {len(expected_parsed_data['references'])}, Got {len(actual_parsed_data['references'])}")
            test_passed = False
        else:
            for i, (actual_ref, expected_ref) in enumerate(zip(actual_parsed_data["references"], expected_parsed_data["references"])):
                ref_num = i + 1
                ref_passed = True
                for key in expected_ref:
                    if key not in actual_ref:
                        print(f"FAIL (Ref {ref_num}): Missing key '{key}' in actual output.")
                        ref_passed = False
                        test_passed = False
                    elif actual_ref[key] != expected_ref[key]:
                        # Special handling for lists (Checks Performed, Verification Details)
                        if isinstance(actual_ref[key], list) and isinstance(expected_ref[key], list):
                            # Convert to set for order-independent comparison of list items
                            if set(actual_ref[key]) != set(expected_ref[key]):
                                print(f"FAIL (Ref {ref_num}): Mismatch in '{key}'.")
                                print(f"  Expected: {expected_ref[key]}")
                                print(f"  Actual:   {actual_ref[key]}")
                                ref_passed = False
                                test_passed = False
                        else:
                            print(f"FAIL (Ref {ref_num}): Mismatch in '{key}'.")
                            print(f"  Expected: '{expected_ref[key]}'")
                            print(f"  Actual:   '{actual_ref[key]}'")
                            ref_passed = False
                            test_passed = False
                if ref_passed:
                    print(f"PASS (Ref {ref_num}): All checks for this reference passed.")
                else:
                    print(f"FAIL (Ref {ref_num}): Some checks for this reference failed.")


        # Compare summary
        print("\n--- Summary Comparison ---")
        if actual_parsed_data["summary"] != expected_parsed_data["summary"]:
            print("FAIL: Mismatch in summary data.")
            print(f"  Expected Summary: {expected_parsed_data['summary']}")
            print(f"  Actual Summary:   {actual_parsed_data['summary']}")
            test_passed = False
        else:
            print("PASS: Summary data matches expected.")

        print("\n--- Test Results ---")
        if test_passed:
            print("All tests passed! The ctr_validator.py script's output is consistent with the expected data.")
        else:
            print("Some tests failed. Please review the discrepancies above.")

    except FileNotFoundError:
        print(f"Error: 'ctr_validator.py' not found. Please ensure the script is in the same directory or its path is correctly configured.")
        test_passed = False
    except Exception as e:
        print(f"An unexpected error occurred in the test script: {e}")
        test_passed = False
    finally:
        # Clean up the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"\nCleaned up temporary file: {temp_file_path}")
        else:
            print("\nNo temporary file to clean up or file already removed.")
        print("--- Harvard Reference Validator Test Finished ---")


if __name__ == "__main__":
    run_test()
