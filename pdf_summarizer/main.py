import anthropic
from typing import List, Dict, Tuple
import json
import os
import pdf2image
import base64
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

anthropic_key = os.getenv("ANTHROPIC_KEY")

def ask_claude_to_summarize_image(encoded_image: str) -> str | None:
    client = anthropic.Anthropic(
        api_key=anthropic_key
    )
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=3000,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": encoded_image,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Analyze the data from this image and return the key takeaways along with the numbers. Keep the original Japanese. Only return a python dictonary with key value pairs for each key point. Make sure to include a タイトル field as well.",
                    },
                ],
            }
        ],
    )

    result = message.content[0].text
    print(message.usage)

    return result


def get_all_pdf_paths() -> List[Tuple[str, str]]:
    """
    Loop through all files in the pdfs directory. Find file names and construct paths.
    """
    complete_pdf_paths = []
    all_pdfs_tuple = os.walk("/Users/justin/Repos/NIT-Factbook-Scraper/pdf-summarizer/pdfs")
    for pdf_tuple in all_pdfs_tuple:
        pdf_file_names = pdf_tuple[2]
        for pdf_file_name in pdf_file_names:
            if pdf_file_name == ".DS_Store":
                continue
            pdf_path = os.path.join(pdf_tuple[0], pdf_file_name)
            university_name = pdf_file_name.split("-")[0].strip()
            print(f"Univesity_name is {university_name}, and the path is {pdf_path}")
            complete_pdf_paths.append((university_name, pdf_path))

    return complete_pdf_paths


def parse_pdf_into_images(pdf_path) -> List[str]:
    """
    Convert pdf to images.
    """
    images = pdf2image.convert_from_path(pdf_path)
    return images

def convert_images_to_base64(images) -> List[bytes]:
    base64_images = []
    for image in images:
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        base64_images.append(img_str)
    return base64_images

def summarize_image(encoded_image: str) -> str:
    print("Querying claude AI for image summary...")
    response = ask_claude_to_summarize_image(encoded_image)
    print("Finished querying.")
    return str(response)


def parse_response(ai_response: str) -> List[Dict[str, str]] | str:
    print("Parsing ai response...")
    print(ai_response)
    try:
        parsed_response = json.loads(ai_response)
        print("Completed parsing ai repsonse.")
        return parsed_response
    except Exception as e:
        print(f"Parser ran into an exception: {e}")
        return ai_response


def extract_pdf_data(images) -> Dict[str, str]:
    print("Parsing images for data.")
    extracted = {}
    for n in range(len(images)):
        page_num = n
        image = images[n]
        claude_response = summarize_image(image)
        parsed_response = parse_response(claude_response)
        try:
            page_title = parsed_response["タイトル"]
            id = f"{page_num} - {page_title}"
            extracted[id] = parsed_response
        except Exception as e:
            page_title = "Could not parse ai response as JSON"
            id = f"{page_num} - {page_title}"
            extracted[id] = parsed_response

    print("Done parsing image parsing.")
    return extracted


def main():
    all_pdfs_paths = get_all_pdf_paths()
    print(f"All paths are, {all_pdfs_paths}")
    all_data = []
    for pdf_path_tuple in all_pdfs_paths:
        university_name = pdf_path_tuple[0]
        path = pdf_path_tuple[1]
        images = parse_pdf_into_images(path)
        encoded_images = convert_images_to_base64(images)
        pdf_data = extract_pdf_data(encoded_images)
        all_data.append({"university": university_name, "factbookData": pdf_data})
    return all_data


if __name__ == "__main__":
    print("Starting...")
    results = main()
    print("Finished!")
    print(f"Raw results \n\n{results}\n\n")
    results_parsed_to_json = json.dumps(results, ensure_ascii=False, indent=4)
    print(f"Parsed json results \n\n{results_parsed_to_json}\n\n")
