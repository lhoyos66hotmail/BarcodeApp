import azure.functions as func
import numpy as np
import cv2
from requests_toolbelt.multipart import decoder   # <‑‑ aquí vive MultipartDecoder

# ---------------------------------------------------------------------
# Helper: decodifica barcodes con pyzbar, o con OpenCV si no lo incluyes
# ---------------------------------------------------------------------
def _decode_barcodes(img: np.ndarray) -> list[str]:
    try:
        from pyzbar import pyzbar                 # opcional: solo si tu build lo tiene
        return [obj.data.decode() for obj in pyzbar.decode(img)]
    except ModuleNotFoundError:
        # método sencillo usando OpenCV (códigos QR solo):
        qr = cv2.QRCodeDetector()
        data, _, _ = qr.detectAndDecode(img)
        return [data] if data else []

# ---------------------------------------------------------------------
# Azure Function handler
# ---------------------------------------------------------------------
def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # 1. body y Content‑Type  --------------------------------------
        body = req.get_body()                     # bytes
        ctype = req.headers.get('Content-Type', '')
        if not ctype.startswith('multipart/'):
            return func.HttpResponse(
                "Se esperaba multipart/form-data",
                status_code=400
            )

        # 2. Parseo multipart con toolbelt -----------------------------
        multi = decoder.MultipartDecoder(body, ctype)
        # buscamos la primera parte cuyo nombre sea “file”
        part = next(
            (p for p in multi.parts
             if b'Content-Disposition' in p.headers
             and b'name="file"' in p.headers[b'Content-Disposition']),
            None
        )
        if part is None:
            return func.HttpResponse("Campo 'file' no encontrado", status_code=400)

        # 3. Imagen → numpy array -------------------------------------
        img_array = np.frombuffer(part.content, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            return func.HttpResponse("Imagen inválida", status_code=400)

        # 4. Decodificar barcodes -------------------------------------
        barcodes = _decode_barcodes(img)
        if not barcodes:
            return func.HttpResponse("No se detectaron códigos", status_code=404)

        return func.HttpResponse("\n".join(barcodes), status_code=200)

    except Exception as exc:                       # log básico
        return func.HttpResponse(
            f"Error interno: {exc}",
            status_code=500
        )
