import httpx
import asyncio
from http import HTTPStatus
import os
import time


async def create_github_aws_storage_bucket(file_path, client):
    url = "https://github.com/upload/policies/assets"
    headers = {
        "GitHub-Verified-Fetch": "true",
        "Origin": "https://github.com",
    }

    cookies = {
        "user_session": "Tlk43iXDAsZZ5Lsl59mI-6Xcq5llmikNF2IvNOz8SRqAILnS",
    }

    file_name = file_path.split("/")[-1]
    file_size = os.path.getsize(file_path)

    form_data = {"name": file_name, "size": file_size, "repository_id": 972714036}

    response = await client.post(url, headers=headers, data=form_data, cookies=cookies)

    if response.status_code == HTTPStatus.CREATED:
        print("Bucket created successfully.")
        return response.json()
    else:
        print("Failed to create bucket.")
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        return None


async def upload_file_to_github_aws_storage(policy, file_path, client):
    url = policy["upload_url"]
    headers = policy["header"].copy()
    form_data = policy["form"].copy()

    # Add authenticity token if needed
    if policy.get("same_origin"):
        form_data["authenticity_token"] = policy["upload_authenticity_token"]

    cookies = {
        "user_session": "Tlk43iXDAsZZ5Lsl59mI-6Xcq5llmikNF2IvNOz8SRqAILnS",
    }

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "application/octet-stream")}
        response = await client.post(
            url, headers=headers, data=form_data, files=files, cookies=cookies
        )

    if response.status_code == HTTPStatus.NO_CONTENT:
        print("File uploaded successfully.")
        return True
    else:
        print("Failed to upload file.")
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        return False


async def get_uploaded_file_url(policy, client):
    url = "https://github.com" + policy["asset_upload_url"]
    token = policy["asset_upload_authenticity_token"]
    headers = {
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "GitHub-Verified-Fetch": "true",
        "Origin": "https://github.com",
    }

    form_data = {
        "authenticity_token": token,
    }

    cookies = {
        "user_session": "Tlk43iXDAsZZ5Lsl59mI-6Xcq5llmikNF2IvNOz8SRqAILnS",
    }

    response = await client.put(url, headers=headers, data=form_data, cookies=cookies)

    if response.status_code == HTTPStatus.OK:
        print("File URL retrieved successfully.")
        return response.json()["href"]
    else:
        print("Failed to retrieve file URL.")
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        return None


async def make_uploaded_file_public(successful_uploads_details, client):
    comment_content = "\n".join(
        [
            f"- {file_name}: {file_url}"
            for file_name, file_url in successful_uploads_details
        ]
    )

    url = "https://api.github.com/repos/lovelywovi/pushFuze/issues/1/comments"
    headers = {
        "Authorization": "token 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",
        "Content-Type": "application/json",
    }
    body = comment_content
    data = {
        "body": body,
    }
    response = await client.post(url, headers=headers, json=data)

    if response.status_code == HTTPStatus.CREATED:
        print("Comment posted successfully.")
        return True
    else:
        print("Failed to post comment.")
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        return False


async def upload_single_file(file_path, file_name, client, i):
    print(f"\n--- Attempting upload {i + 1} ---")
    policy = await create_github_aws_storage_bucket(file_path, client)
    if policy:
        upload_success = await upload_file_to_github_aws_storage(
            policy, file_path, client
        )
        if upload_success:
            file_url = await get_uploaded_file_url(policy, client)
            if file_url:
                print(f"Upload {i + 1} successful.")
                print("File URL:", file_url)
                return (file_name, file_url)
            else:
                print(
                    f"Upload {i + 1}: Failed to retrieve file URL after successful upload."
                )
        else:
            print(f"Upload {i + 1}: File upload failed.")
    else:
        print(f"Upload {i + 1}: Failed to create bucket.")
    return None


async def main():
    file_path = "bomb5.md"
    file_name = os.path.basename(file_path)
    num_uploads = 30
    print(f"Starting {num_uploads} uploads of '{file_name}'...")
    start_time = time.time()
    async with httpx.AsyncClient() as client:
        tasks = [
            upload_single_file(file_path, file_name, client, i)
            for i in range(num_uploads)
        ]
        results = await asyncio.gather(*tasks)
        successful_uploads_details = [r for r in results if r]

        end_time = time.time()
        duration = end_time - start_time
        successful_uploads_count = len(successful_uploads_details)

        print("\n--- Upload Summary ---")
        print(f"Finished {num_uploads} upload attempts.")
        print(f"Successful uploads: {successful_uploads_count}")
        print(f"Total time taken: {duration:.2f} seconds")
        if successful_uploads_count > 0:
            print(
                f"Average time per successful upload: {duration / successful_uploads_count:.2f} seconds"
            )
            # Post a single comment summarizing all successful uploads
            print("\n--- Posting Summary Comment ---")
            await make_uploaded_file_public(successful_uploads_details, client)
        else:
            print("No uploads were successful.")


if __name__ == "__main__":
    asyncio.run(main())
