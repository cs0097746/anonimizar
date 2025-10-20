"""
SCRIPT AUTOMÁTICO COMPLETO
DICOM → Extrai PDF → Converte para PNG → Anonimiza → Salva

Coloque seus DICOMs em pasta_com_dicoms/ e execute!
"""

import os
import pydicom
from PIL import Image, ImageDraw, ImageFont
import io

input_folder = "pasta_com_dicoms"
output_folder = "ecgs_anonimizados"

os.makedirs(output_folder, exist_ok=True)

def anonimizar_metadados(ds, contador):
    """Anonimiza metadados do DICOM"""
    campos_anonimos = [
        "PatientID", "PatientName", "PatientSex", "PatientBirthDate", "PatientAge",
        "EthnicGroup", "ReferringPhysicianName", "InstitutionName", "InstitutionAddress",
        "StudyDate", "SeriesDate", "AcquisitionDate", "ContentDate",
        "PatientAddress", "PatientTelephoneNumbers", "AccessionNumber", "StudyID"
    ]
    
    for campo in campos_anonimos:
        if campo in ds:
            elemento = ds.data_element(campo)
            if elemento is not None:
                if elemento.VR == 'DA':
                    elemento.value = "20000101"
                elif elemento.VR == 'TM':
                    elemento.value = "000000"
                else:
                    elemento.value = "ANONIMIZADO"
    
    ds.PatientID = f"ANON_{contador:04d}"
    ds.PatientName = f"ANONIMIZADO_{contador:04d}"
    
    return ds

def converter_pdf_para_imagem_PIL(pdf_data):
    """
    Converte PDF para imagem usando PIL + pdf2image
    """
    try:
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(pdf_data, dpi=200)
        if images:
            return images[0]
        return None
    except Exception as e:
        print(f"    ⚠️  pdf2image falhou: {e}")
        return None

def converter_pdf_para_imagem_PyMuPDF(pdf_data):
    """
    Converte PDF para imagem usando PyMuPDF (fitz) - NÃO PRECISA POPPLER!
    """
    try:
        import fitz  # PyMuPDF
        
        # Abre PDF dos bytes
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        
        # Pega primeira página
        page = doc[0]
        
        # Converte para imagem (matriz de pixels)
        # zoom=2 para boa qualidade
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        
        # Converte para PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        doc.close()
        
        return img
        
    except ImportError:
        print(f"    ⚠️  PyMuPDF não instalado")
        return None
    except Exception as e:
        print(f"    ⚠️  PyMuPDF falhou: {e}")
        return None

def anonimizar_imagem(img, largura_percentual=0.30, altura_percentual=0.29):
    """Oculta região superior esquerda com dados sensíveis"""
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    largura_ocultar = int(img.size[0] * largura_percentual)
    altura_ocultar = int(img.size[1] * altura_percentual)
    
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (largura_ocultar, altura_ocultar)], fill='black')
    
    # Texto de anonimização
    try:
        tamanho_fonte = max(20, int(altura_ocultar * 0.08))
        try:
            font_titulo = ImageFont.truetype("arial.ttf", tamanho_fonte)
            font_sub = ImageFont.truetype("arial.ttf", int(tamanho_fonte * 0.6))
        except:
            font_titulo = ImageFont.load_default()
            font_sub = ImageFont.load_default()
    except:
        font_titulo = ImageFont.load_default()
        font_sub = ImageFont.load_default()
    
    margem = 10
    y = margem
    
    if font_titulo:
        draw.text((margem, y), "DADOS ANONIMIZADOS", fill='white', font=font_titulo)
        y += tamanho_fonte + 5
        draw.text((margem, y), "Conforme LGPD", fill='lightgray', font=font_sub)
        y += int(tamanho_fonte * 0.6) + 10
        
        infos = ["• ID Paciente", "• Nome", "• Dados Clínicos"]
        for info in infos:
            draw.text((margem, y), info, fill='darkgray', font=font_sub)
            y += int(tamanho_fonte * 0.5) + 2
    else:
        draw.text((margem, y), "DADOS ANONIMIZADOS - LGPD", fill='white')
    
    return img, largura_ocultar, altura_ocultar

# ============================================================================
# PROCESSAMENTO PRINCIPAL
# ============================================================================

print("="*80)
print("ANONIMIZADOR AUTOMÁTICO DE ECGs - HUSM")
print("DICOM → PDF → PNG → Anonimizado")
print("="*80)
print(f"\n📁 Pasta entrada: {input_folder}")
print(f"📁 Pasta saída: {output_folder}\n")

# Verifica se PyMuPDF está instalado
try:
    import fitz
    print("✓ PyMuPDF instalado - Conversão automática habilitada!\n")
    usar_pymupdf = True
except ImportError:
    print("⚠️  PyMuPDF não instalado")
    print("   Instalando automaticamente...\n")
    import subprocess
    import sys
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyMuPDF"])
        print("✓ PyMuPDF instalado com sucesso!\n")
        import fitz
        usar_pymupdf = True
    except:
        print("❌ Falha ao instalar PyMuPDF")
        print("   Tentará usar pdf2image (requer Poppler)\n")
        usar_pymupdf = False

contador = 0
sucesso = 0
falhas = 0

# ============================================================================
# BUSCA RECURSIVA - Encontra todos os DICOMs em subpastas
# ============================================================================
print("🔍 Buscando arquivos DICOM (incluindo subpastas)...\n")

arquivos_dicom = []
for root, dirs, files in os.walk(input_folder):
    for filename in files:
        if filename.lower().endswith('.dcm'):
            caminho_completo = os.path.join(root, filename)
            # Calcula caminho relativo para exibir
            caminho_relativo = os.path.relpath(caminho_completo, input_folder)
            arquivos_dicom.append({
                'caminho_completo': caminho_completo,
                'caminho_relativo': caminho_relativo,
                'nome_paciente': os.path.basename(root),  # Nome da pasta do paciente
                'filename': filename
            })

if not arquivos_dicom:
    print(f"❌ Nenhum arquivo DICOM encontrado em '{input_folder}/' (incluindo subpastas)")
    print(f"\n💡 Estrutura esperada:")
    print(f"   {input_folder}/")
    print(f"   ├── paciente_001/")
    print(f"   │   └── ecg.dcm")
    print(f"   ├── paciente_002/")
    print(f"   │   └── ecg.dcm")
    print(f"   └── ...")
    print(f"\n   Coloque o ZIP extraído na pasta '{input_folder}/' e execute novamente!")
    exit(1)

print(f"✅ Encontrados {len(arquivos_dicom)} arquivo(s) DICOM em subpastas!\n")

# Mostra preview das pastas encontradas
pastas_unicas = set(info['nome_paciente'] for info in arquivos_dicom)
print(f"📂 Pastas de pacientes encontradas: {len(pastas_unicas)}")
for i, pasta in enumerate(sorted(pastas_unicas)[:5], 1):
    print(f"   {i}. {pasta}")
if len(pastas_unicas) > 5:
    print(f"   ... e mais {len(pastas_unicas) - 5} pastas")
print()

for info in arquivos_dicom:
    contador += 1
    print(f"{'='*80}")
    print(f"[{contador}/{len(arquivos_dicom)}] {info['caminho_relativo']}")
    print(f"{'='*80}")
    
    caminho_arquivo = info['caminho_completo']
    filename = info['filename']
    
    try:
        # 1. LÊ DICOM
        print(f"  📖 Lendo DICOM...")
        ds = pydicom.dcmread(caminho_arquivo)
        print(f"     ✓ ID: {ds.get('PatientID', 'N/A')}")
        print(f"     ✓ Nome: {ds.get('PatientName', 'N/A')}")
        
        # 2. ANONIMIZA METADADOS (apenas para ter ID único)
        print(f"\n  🔒 Gerando ID anonimizado...")
        ds = anonimizar_metadados(ds, contador)
        print(f"     ✓ Novo ID: {ds.PatientID}")
        
        # 3. EXTRAI PDF
        print(f"\n  📄 Extraindo PDF embutido...")
        if not hasattr(ds, 'EncapsulatedDocument'):
            print(f"     ❌ Este DICOM não tem PDF embutido")
            falhas += 1
            continue
        
        pdf_data = ds.EncapsulatedDocument
        print(f"     ✓ PDF extraído ({len(pdf_data):,} bytes)")
        
        # 4. CONVERTE PDF PARA IMAGEM
        print(f"\n  🖼️  Convertendo PDF para PNG...")
        
        img = None
        
        # Tenta PyMuPDF primeiro (não precisa Poppler!)
        if usar_pymupdf:
            img = converter_pdf_para_imagem_PyMuPDF(pdf_data)
            if img:
                print(f"     ✓ Convertido com PyMuPDF")
        
        # Se falhou, tenta pdf2image
        if img is None:
            img = converter_pdf_para_imagem_PIL(pdf_data)
            if img:
                print(f"     ✓ Convertido com pdf2image")
        
        if img is None:
            print(f"     ❌ Falha na conversão")
            print(f"     💡 Instale: pip install PyMuPDF")
            falhas += 1
            continue
        
        print(f"     ✓ Imagem: {img.size[0]} x {img.size[1]} pixels")
        
        # 5. ANONIMIZA IMAGEM
        print(f"\n  🔐 Anonimizando região com dados sensíveis...")
        img_anon, larg_oc, alt_oc = anonimizar_imagem(img)
        print(f"     ✓ Região ocultada: {larg_oc} x {alt_oc} px")
        print(f"     ✓ Percentual: 20% largura x 25% altura")
        
        # 6. SALVA PNG ANONIMIZADO
        nome_png = f"anonimizado_{contador:04d}.png"
        caminho_png = os.path.join(output_folder, nome_png)
        img_anon.save(caminho_png, quality=95, optimize=True)
        
        print(f"\n  ✅ PNG ANONIMIZADO SALVO: {nome_png}")
        print(f"     📊 Tamanho: {os.path.getsize(caminho_png):,} bytes")
        
        sucesso += 1
        
    except Exception as e:
        print(f"\n  ❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        falhas += 1
    
    print()

# RESUMO FINAL
print("="*80)
print("PROCESSAMENTO CONCLUÍDO!")
print("="*80)
print(f"\n📊 ESTATÍSTICAS:")
print(f"   Total de arquivos: {contador}")
print(f"   ✅ Sucesso: {sucesso}")
print(f"   ❌ Falhas: {falhas}")

if sucesso > 0:
    print(f"\n✨ RESULTADO:")
    print(f"   📁 {sucesso} arquivo(s) anonimizado(s) com sucesso!")
    print(f"   📂 Localização: {os.path.abspath(output_folder)}/")
    print(f"\n   Arquivos gerados:")
    print(f"   • anonimizado_XXXX.png - Imagens PNG anonimizadas (prontas para uso)")

if falhas > 0:
    print(f"\n⚠️  ATENÇÃO: {falhas} arquivo(s) com falha")
    print(f"   Verifique os logs acima para detalhes")

print(f"\n{'='*80}")
print("Dataset pronto para uso no TCC! 🎓")
print("="*80)
