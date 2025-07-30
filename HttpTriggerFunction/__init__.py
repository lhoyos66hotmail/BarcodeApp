import azure.functions as func
import numpy as np
import cv2
from requests_toolbelt.multipart import decoder

def decode_barcodes(img: np.ndarray) -> list[str]:
    qr = cv2.QRCodeDetector()
    data, points, _ = qr.detectAndDecode(img)
    return [data] if data else []

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_body()
        ctype = req.headers.get('Content-Type', '')
        if not ctype.startswith('multipart/'):
            return func.HttpResponse("Se esperaba multipart/form-data", status_code=400)

        multi = decoder.MultipartDecoder(body, ctype)
        part = next(
            (p for p in multi.parts
             if b'Content-Disposition' in p.headers
             and b'name="file"' in p.headers[b'Content-Disposition']),
            None
        )
        if part is None:
            return func.HttpResponse("Campo 'file' no encontrado", status_code=400)

        img_array = np.frombuffer(part.content, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            return func.HttpResponse("Imagen inválida", status_code=400)

        barcodes = decode_barcodes(img)
        if not barcodes:
            return func.HttpResponse("No se detectaron códigos", status_code=404)

        return func.HttpResponse("\n".join(barcodes), status_code=200)

    except Exception as exc:
        return func.HttpResponse(f"Error interno: {exc}", status_code=500)
