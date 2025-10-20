"""
Script para analisar COMPLETAMENTE um arquivo DICOM e descobrir onde está a imagem
"""

import os
import pydicom
import sys

pasta = "pasta_com_dicoms"

arquivos = [f for f in os.listdir(pasta) if f.lower().endswith('.dcm')]

if not arquivos:
    print("❌ Nenhum arquivo DICOM encontrado!")
    sys.exit(1)

arquivo = os.path.join(pasta, arquivos[0])

print("="*80)
print(f"ANÁLISE COMPLETA DO DICOM")
print("="*80)
print(f"\nArquivo: {arquivos[0]}\n")

ds = pydicom.dcmread(arquivo)

# Informações básicas
print("📋 INFORMAÇÕES BÁSICAS:")
print(f"  • PatientID: {ds.get('PatientID', 'N/A')}")
print(f"  • PatientName: {ds.get('PatientName', 'N/A')}")
print(f"  • Modality: {ds.get('Modality', 'N/A')}")
print(f"  • Manufacturer: {ds.get('Manufacturer', 'N/A')}")
print(f"  • Transfer Syntax: {ds.file_meta.get('TransferSyntaxUID', 'N/A')}")

# Verifica Pixel Data
print(f"\n🖼️ PIXEL DATA:")
if hasattr(ds, 'PixelData'):
    print(f"  ✅ PixelData presente")
    print(f"     - Tamanho: {len(ds.PixelData)} bytes")
    if hasattr(ds, 'Rows'):
        print(f"     - Rows: {ds.Rows}")
    if hasattr(ds, 'Columns'):
        print(f"     - Columns: {ds.Columns}")
    if hasattr(ds, 'BitsAllocated'):
        print(f"     - BitsAllocated: {ds.BitsAllocated}")
    if hasattr(ds, 'PhotometricInterpretation'):
        print(f"     - PhotometricInterpretation: {ds.PhotometricInterpretation}")
    if hasattr(ds, 'SamplesPerPixel'):
        print(f"     - SamplesPerPixel: {ds.SamplesPerPixel}")
else:
    print(f"  ❌ PixelData NÃO encontrado")

# Verifica Waveform
print(f"\n📊 WAVEFORM DATA:")
if 'WaveformSequence' in ds:
    print(f"  ✅ WaveformSequence presente")
    for i, wf in enumerate(ds.WaveformSequence):
        print(f"     Waveform {i+1}:")
        if hasattr(wf, 'NumberOfWaveformChannels'):
            print(f"       - Channels: {wf.NumberOfWaveformChannels}")
        if hasattr(wf, 'NumberOfWaveformSamples'):
            print(f"       - Samples: {wf.NumberOfWaveformSamples}")
        if hasattr(wf, 'SamplingFrequency'):
            print(f"       - Frequency: {wf.SamplingFrequency} Hz")
else:
    print(f"  ❌ WaveformSequence NÃO encontrado")

# Verifica Encapsulated Document
print(f"\n📄 ENCAPSULATED DOCUMENT:")
if hasattr(ds, 'EncapsulatedDocument'):
    print(f"  ✅ EncapsulatedDocument presente")
    print(f"     - Tamanho: {len(ds.EncapsulatedDocument)} bytes")
    if hasattr(ds, 'MIMETypeOfEncapsulatedDocument'):
        print(f"     - MIME Type: {ds.MIMETypeOfEncapsulatedDocument}")
else:
    print(f"  ❌ EncapsulatedDocument NÃO encontrado")

# Lista TODOS os elementos
print(f"\n📑 TODOS OS ELEMENTOS DO DICOM:")
print("="*80)

for elem in ds:
    if elem.VR not in ['OB', 'OW', 'UN', 'SQ']:  # Ignora dados binários grandes
        valor = str(elem.value)
        if len(valor) > 60:
            valor = valor[:60] + "..."
        print(f"  {elem.tag} {elem.name:<40} VR:{elem.VR} = {valor}")

print("\n" + "="*80)

# Verifica se tem dados binários grandes (possível imagem)
print(f"\n🔍 ELEMENTOS BINÁRIOS (possível imagem):")
for elem in ds:
    if elem.VR in ['OB', 'OW', 'UN']:
        tamanho = len(elem.value) if hasattr(elem.value, '__len__') else 0
        print(f"  • {elem.name}: {tamanho:,} bytes")

# Tenta diferentes métodos de acesso
print(f"\n🧪 TENTANDO ACESSAR PIXEL_ARRAY:")
try:
    pixel_array = ds.pixel_array
    print(f"  ✅ pixel_array acessível!")
    print(f"     - Shape: {pixel_array.shape}")
    print(f"     - Dtype: {pixel_array.dtype}")
    print(f"     - Min: {pixel_array.min()}")
    print(f"     - Max: {pixel_array.max()}")
except Exception as e:
    print(f"  ❌ Erro ao acessar pixel_array: {e}")

print("\n" + "="*80)
print("CONCLUSÃO:")
print("="*80)

if hasattr(ds, 'PixelData'):
    print("✅ Este DICOM DEVERIA ter imagem (PixelData presente)")
    print("   Possíveis problemas:")
    print("   1. Compressão não suportada")
    print("   2. Transfer Syntax especial")
    print("   3. Precisa de decoder específico")
elif 'WaveformSequence' in ds:
    print("⚠️  Este DICOM tem apenas Waveform (dados de onda)")
    print("   Não é uma imagem, precisa renderizar o waveform")
else:
    print("❌ Este DICOM não tem imagem nem waveform")
    print("   Contém apenas metadados")

print("="*80)
