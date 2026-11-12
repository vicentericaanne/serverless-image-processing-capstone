from io import BytesIO
from urllib.parse import unquote_plus

import boto3
from PIL import Image, ImageOps

s3 = boto3.client("s3")

ORIGINALS_BUCKET = "rica-capstone-originals"
RESIZED_BUCKET = "rica-capstone-resized"
THUMBNAIL_SIZE = (200, 200)


def resize_image(key):
    response = s3.get_object(Bucket=ORIGINALS_BUCKET, Key=key)
    with response["Body"] as body:
        image_data = body.read()

    with Image.open(BytesIO(image_data)) as original:
        image = ImageOps.exif_transpose(original).convert("RGBA")
        image.thumbnail(THUMBNAIL_SIZE)

        with BytesIO() as output:
            image.save(output, format="PNG")
            thumbnail_key = f"thumbnails/{key}.png"
            s3.put_object(
                Bucket=RESIZED_BUCKET,
                Key=thumbnail_key,
                Body=output.getvalue(),
                ContentType="image/png",
            )

    return {
        "success": True,
        "thumbnailKey": thumbnail_key,
        "width": image.width,
        "height": image.height,
    }


def lambda_handler(event, context):
    # S3 notifications contain URL-encoded object keys.
    if "Records" in event:
        results = []
        for record in event["Records"]:
            key = unquote_plus(record["s3"]["object"]["key"])
            results.append(resize_image(key))
        return {"success": True, "thumbnails": results}

    # Manual tests and Step Functions pass the object key directly.
    return resize_image(event["key"])
