import os
import pydicom
import numpy as np
from pydicom.pixel_data_handlers.util import apply_voi_lut
from PIL import Image, ImageDraw

input_folder = "pasta_com_dicoms"
output_folder = "ecgs_anonimizados"

os.makedirs(output_folder, exist_ok=True)

campos_anonimos = [
    "PatientID", "PatientName", "PatientSex", "PatientBirthDate", "EthnicGroup",
    "ReferringPhysicianName", "InstitutionName", "InstitutionAddress", "StudyDate"
]

for filename in os.listdir(input_folder):
    if filename.lower().endswith(".dcm"):
        caminho_arquivo = os.path.join(input_folder, filename)
        ds = pydicom.dcmread(caminho_arquivo)

        # Anonimiza metadados
        for campo in campos_anonimos:
            if campo in ds:
                if ds.data_element(campo).VR == 'DA':
                    ds.data_element(campo).value = ""
                else:
                    ds.data_element(campo).value = "ANONYMIZED"

        # SALVA O DICOM ANONIMIZADO
        caminho_saida_dcm = os.path.join(output_folder, filename)
        ds.save_as(caminho_saida_dcm)

        # Tenta extrair imagem/anexar PNG
        try:
            pixel_array = apply_voi_lut(ds.pixel_array, ds)
            if pixel_array.dtype != np.uint8:
                pixel_array = (255 * (pixel_array - pixel_array.min()) / (pixel_array.ptp())).astype(np.uint8)
            img = Image.fromarray(pixel_array)
        except Exception as e:
            print(f"Arquivo {filename} sem imagem (Pixel Data), pulando PNG.")
            continue

        # Cobre faixa do laudo
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, 0), (300, 120)], fill=0)

        nome_saida = os.path.splitext(filename)[0] + ".png"
        img.save(os.path.join(output_folder, nome_saida))

print("Processamento concluído! Verifique a pasta de saída.")
