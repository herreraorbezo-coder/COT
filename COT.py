from PIL import Image
import numpy as np
import cv2
from pyzbar.pyzbar import decode

st.subheader("📷 Escanear QR del equipo")

imagen = st.camera_input("Toma una foto al QR del equipo")

tag = None

if imagen is not None:
    img = Image.open(imagen)
    img_np = np.array(img)

    # Convertir a formato OpenCV
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    # Detectar QR
    codigos = decode(img_cv)

    if codigos:
        texto_qr = codigos[0].data.decode("utf-8")
        st.success(f"QR detectado: {texto_qr}")

        # Si el QR contiene solo el TAG
        if texto_qr in equipos:
            tag = texto_qr
        # Si el QR contiene una URL con ?tag=
        elif "tag=" in texto_qr:
            tag = texto_qr.split("tag=")[-1]

    else:
        st.warning("No se detectó QR. Intenta nuevamente.")

    st.success("✅ Registro guardado correctamente")



