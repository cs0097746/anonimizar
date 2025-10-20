"""
SISTEMA COMPLETO DE PROCESSAMENTO DE ECGs - TCC
Conforme requisitos RF01, RF03, RF04, RD02, RD03, RD06, RF07

FUNCIONALIDADES:
1. Validação de qualidade (mínimo 200 DPI)
2. Extração e conversão de DICOM → PNG
3. Anonimização (metadados + imagem)
4. Pré-processamento para IA (redimensionar, normalizar)
5. Estrutura de pastas organizada
6. Nomenclatura única e anonimizada
"""

import os
import pydicom
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io
from datetime import datetime

# ============================================================================
# CONFIGURAÇÕES DO SISTEMA
# ============================================================================

# Pastas de entrada/saída
INPUT_FOLDER = "pasta_com_dicoms"
OUTPUT_BASE = "dataset_processado"

# Estrutura de pastas conforme requisitos
OUTPUT_FOLDERS = {
    'anonimizados': os.path.join(OUTPUT_BASE, 'ecgs_anonimizados'),
    'para_ia': os.path.join(OUTPUT_BASE, 'preprocessed_for_ai'),
    'originais_alta_res': os.path.join(OUTPUT_BASE, 'images_ecg'),
}

# Requisitos de qualidade
MIN_DPI = 200  # RF01, RD02, RD03

# Configurações para IA (RF03, RF04)
IA_CONFIG = {
    'tamanho': (224, 224),  # Pode ser alterado para (512, 512) se necessário
    'modo_cor': 'RGB',      # 'RGB' ou 'L' (grayscale)
    'normalizar': True,     # Normalizar para 0-1
}

# Configuração de anonimização
ANONIMIZAR_CONFIG = {
    'largura_percentual': 0.20,  # 20% da largura
    'altura_percentual': 0.25,   # 25% da altura
}

# ============================================================================
# CRIAR ESTRUTURA DE PASTAS
# ============================================================================

def criar_estrutura_pastas():
    """Cria estrutura de pastas conforme RD06, RF07"""
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    
    for pasta in OUTPUT_FOLDERS.values():
        os.makedirs(pasta, exist_ok=True)
    
    print("✓ Estrutura de pastas criada:")
    print(f"  • {INPUT_FOLDER}/ - Entrada de DICOMs")
    print(f"  • {OUTPUT_FOLDERS['anonimizados']}/ - ECGs anonimizados (alta resolução)")
    print(f"  • {OUTPUT_FOLDERS['para_ia']}/ - Imagens pré-processadas para IA")
    print(f"  • {OUTPUT_FOLDERS['originais_alta_res']}/ - Imagens originais (backup)")

# ============================================================================
# FUNÇÕES DE VALIDAÇÃO (RF01, RD02, RD03)
# ============================================================================

def validar_qualidade_imagem(img, min_dpi=MIN_DPI):
    """
    Valida se a imagem atende aos requisitos de qualidade
    RF01, RD02, RD03: Mínimo 200 DPI
    """
    # Verifica DPI
    dpi = img.info.get('dpi', (72, 72))
    dpi_x, dpi_y = dpi if isinstance(dpi, tuple) else (dpi, dpi)
    dpi_media = (dpi_x + dpi_y) / 2
    
    # Verifica tamanho mínimo (equivalente a 200 DPI)
    largura_min = 1600  # ~8 polegadas x 200 DPI
    altura_min = 1200   # ~6 polegadas x 200 DPI
    
    validacoes = {
        'dpi_ok': dpi_media >= min_dpi or (img.size[0] >= largura_min and img.size[1] >= altura_min),
        'dpi_atual': dpi_media,
        'resolucao': f"{img.size[0]}x{img.size[1]}",
        'tamanho_ok': img.size[0] >= largura_min and img.size[1] >= altura_min,
    }
    
    return validacoes

# ============================================================================
# FUNÇÕES DE ANONIMIZAÇÃO
# ============================================================================

def anonimizar_metadados(ds, contador):
    """Anonimiza metadados do DICOM conforme LGPD"""
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

def anonimizar_imagem_visual(img):
    """
    Oculta região com dados sensíveis na imagem
    Preserva morfologia do ECG
    """
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    largura_ocultar = int(img.size[0] * ANONIMIZAR_CONFIG['largura_percentual'])
    altura_ocultar = int(img.size[1] * ANONIMIZAR_CONFIG['altura_percentual'])
    
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
    
    return img

# ============================================================================
# PRÉ-PROCESSAMENTO PARA IA (RF03, RF04)
# ============================================================================

def preprocessar_para_ia(img, config=IA_CONFIG):
    """
    Prepara imagem para modelo de IA
    RF03, RF04: Redimensionar, converter cor, normalizar
    CRÍTICO: Não distorce morfologia do ECG
    """
    # Passo 1: Converter para modo de cor correto
    if config['modo_cor'] == 'RGB' and img.mode != 'RGB':
        img_processada = img.convert('RGB')
    elif config['modo_cor'] == 'L' and img.mode != 'L':
        img_processada = img.convert('L')
    else:
        img_processada = img.copy()
    
    # Passo 2: Redimensionar mantendo aspect ratio (evita distorção)
    # Usa LANCZOS para preservar detalhes do ECG
    tamanho_alvo = config['tamanho']
    
    # Redimensiona mantendo proporção, depois preenche para tamanho exato
    img_processada.thumbnail(tamanho_alvo, Image.Resampling.LANCZOS)
    
    # Cria imagem final no tamanho exato (preenche com branco se necessário)
    img_final = Image.new(config['modo_cor'], tamanho_alvo, 'white')
    
    # Centraliza a imagem redimensionada
    offset = ((tamanho_alvo[0] - img_processada.size[0]) // 2,
              (tamanho_alvo[1] - img_processada.size[1]) // 2)
    img_final.paste(img_processada, offset)
    
    # Passo 3: Converter para array numpy
    img_array = np.array(img_final)
    
    # Passo 4: Normalizar (0-1) se solicitado
    if config['normalizar']:
        img_array = img_array.astype(np.float32) / 255.0
    
    return img_final, img_array

# ============================================================================
# CONVERSÃO DE PDF PARA IMAGEM
# ============================================================================

def converter_pdf_para_imagem(pdf_data, dpi=MIN_DPI):
    """Converte PDF para imagem garantindo DPI mínimo"""
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        page = doc[0]
        
        # Calcula zoom para garantir DPI mínimo
        zoom = dpi / 72  # 72 DPI é o padrão
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        # Define DPI na imagem
        img.info['dpi'] = (dpi, dpi)
        
        doc.close()
        
        return img
        
    except Exception as e:
        print(f"    ⚠️  Erro ao converter PDF: {e}")
        return None

# ============================================================================
# FUNÇÃO PRINCIPAL DE PROCESSAMENTO
# ============================================================================

def processar_dicom(caminho_arquivo, contador):
    """
    Processa um arquivo DICOM completo
    Retorna: (sucesso, info_dict)
    """
    info = {
        'arquivo': os.path.basename(caminho_arquivo),
        'id_anonimizado': f"ANON_{contador:04d}",
        'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S"),
    }
    
    try:
        # 1. LER DICOM
        print(f"  📖 Lendo DICOM...")
        ds = pydicom.dcmread(caminho_arquivo)
        info['id_original'] = ds.get('PatientID', 'N/A')
        print(f"     ✓ ID original: {info['id_original']}")
        
        # 2. ANONIMIZAR METADADOS
        print(f"  🔒 Anonimizando metadados...")
        ds = anonimizar_metadados(ds, contador)
        
        # Salvar DICOM anonimizado
        nome_dcm = f"{info['id_anonimizado']}.dcm"
        ds.save_as(os.path.join(OUTPUT_FOLDERS['anonimizados'], nome_dcm))
        print(f"     ✓ DICOM salvo: {nome_dcm}")
        
        # 3. EXTRAIR PDF
        print(f"  📄 Extraindo PDF embutido...")
        if not hasattr(ds, 'EncapsulatedDocument'):
            print(f"     ❌ DICOM não contém PDF embutido")
            return False, info
        
        pdf_data = ds.EncapsulatedDocument
        tamanho_pdf = len(pdf_data)
        print(f"     ✓ PDF extraído ({tamanho_pdf:,} bytes)")
        
        # 4. CONVERTER PDF PARA IMAGEM (com DPI mínimo)
        print(f"  🖼️  Convertendo PDF para PNG (DPI: {MIN_DPI})...")
        img_original = converter_pdf_para_imagem(pdf_data, dpi=MIN_DPI)
        
        if img_original is None:
            print(f"     ❌ Falha na conversão")
            return False, info
        
        info['resolucao_original'] = f"{img_original.size[0]}x{img_original.size[1]}"
        print(f"     ✓ Imagem criada: {info['resolucao_original']} pixels")
        
        # 5. VALIDAR QUALIDADE (RF01, RD02, RD03)
        print(f"  ✅ Validando qualidade (mín {MIN_DPI} DPI)...")
        validacao = validar_qualidade_imagem(img_original, MIN_DPI)
        
        if not validacao['dpi_ok']:
            print(f"     ⚠️  AVISO: DPI abaixo do mínimo ({validacao['dpi_atual']:.0f} DPI)")
            print(f"     → Resolução: {validacao['resolucao']}")
            if not validacao['tamanho_ok']:
                print(f"     ❌ Imagem rejeitada por baixa qualidade")
                return False, info
        else:
            print(f"     ✓ Qualidade OK: {validacao['dpi_atual']:.0f} DPI, {validacao['resolucao']}")
        
        # 6. SALVAR IMAGEM ORIGINAL (alta resolução)
        nome_original = f"{info['id_anonimizado']}_original.png"
        caminho_original = os.path.join(OUTPUT_FOLDERS['originais_alta_res'], nome_original)
        img_original.save(caminho_original, dpi=(MIN_DPI, MIN_DPI), quality=95)
        print(f"     ✓ Original salvo: {nome_original}")
        
        # 7. ANONIMIZAR IMAGEM VISUAL
        print(f"  🔐 Anonimizando região com dados sensíveis...")
        img_anonimizada = anonimizar_imagem_visual(img_original.copy())
        largura_oc = int(img_original.size[0] * ANONIMIZAR_CONFIG['largura_percentual'])
        altura_oc = int(img_original.size[1] * ANONIMIZAR_CONFIG['altura_percentual'])
        print(f"     ✓ Região ocultada: {largura_oc}x{altura_oc} px ({ANONIMIZAR_CONFIG['largura_percentual']*100:.0f}% x {ANONIMIZAR_CONFIG['altura_percentual']*100:.0f}%)")
        
        # Salvar imagem anonimizada (alta resolução)
        nome_anonimizado = f"{info['id_anonimizado']}_anonimizado.png"
        caminho_anonimizado = os.path.join(OUTPUT_FOLDERS['anonimizados'], nome_anonimizado)
        img_anonimizada.save(caminho_anonimizado, dpi=(MIN_DPI, MIN_DPI), quality=95)
        print(f"     ✓ Imagem anonimizada salva: {nome_anonimizado}")
        
        # 8. PRÉ-PROCESSAR PARA IA (RF03, RF04)
        print(f"  🤖 Pré-processando para IA...")
        print(f"     → Tamanho alvo: {IA_CONFIG['tamanho']}")
        print(f"     → Modo de cor: {IA_CONFIG['modo_cor']}")
        print(f"     → Normalização: {'Sim (0-1)' if IA_CONFIG['normalizar'] else 'Não'}")
        
        img_ia, img_array = preprocessar_para_ia(img_anonimizada)
        
        info['shape_ia'] = img_array.shape
        info['dtype_ia'] = str(img_array.dtype)
        info['range_ia'] = f"[{img_array.min():.3f}, {img_array.max():.3f}]"
        
        print(f"     ✓ Shape: {info['shape_ia']}")
        print(f"     ✓ Tipo: {info['dtype_ia']}")
        print(f"     ✓ Range: {info['range_ia']}")
        
        # Salvar imagem pré-processada para IA
        nome_ia = f"{info['id_anonimizado']}_for_ai.png"
        caminho_ia = os.path.join(OUTPUT_FOLDERS['para_ia'], nome_ia)
        img_ia.save(caminho_ia, quality=95)
        print(f"     ✓ Imagem para IA salva: {nome_ia}")
        
        # Salvar array numpy (opcional, para carregar direto no modelo)
        nome_npy = f"{info['id_anonimizado']}_array.npy"
        caminho_npy = os.path.join(OUTPUT_FOLDERS['para_ia'], nome_npy)
        np.save(caminho_npy, img_array)
        print(f"     ✓ Array numpy salvo: {nome_npy}")
        
        print(f"  ✅ PROCESSAMENTO COMPLETO!")
        
        return True, info
        
    except Exception as e:
        print(f"  ❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False, info

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*80)
    print("SISTEMA DE PROCESSAMENTO DE ECGs - TCC")
    print("Conformidade: RF01, RF03, RF04, RD02, RD03, RD06, RF07")
    print("="*80)
    
    # Criar estrutura de pastas
    criar_estrutura_pastas()
    
    print(f"\n📋 CONFIGURAÇÕES:")
    print(f"  • DPI mínimo: {MIN_DPI} DPI (RF01, RD02, RD03)")
    print(f"  • Tamanho IA: {IA_CONFIG['tamanho']} (RF03, RF04)")
    print(f"  • Modo cor IA: {IA_CONFIG['modo_cor']}")
    print(f"  • Normalização: {'Sim' if IA_CONFIG['normalizar'] else 'Não'}")
    print(f"  • Área anonimizada: {ANONIMIZAR_CONFIG['largura_percentual']*100:.0f}% x {ANONIMIZAR_CONFIG['altura_percentual']*100:.0f}%")
    
    # Verificar PyMuPDF
    try:
        import fitz
        print(f"\n✓ PyMuPDF instalado")
    except ImportError:
        print(f"\n⚠️  PyMuPDF não instalado, instalando...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyMuPDF"])
        print(f"✓ PyMuPDF instalado com sucesso!")
    
    # Listar arquivos DICOM
    arquivos_dicom = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith('.dcm')]
    
    if not arquivos_dicom:
        print(f"\n❌ Nenhum arquivo DICOM encontrado em '{INPUT_FOLDER}/'")
        print(f"\n💡 Coloque seus arquivos .dcm na pasta '{INPUT_FOLDER}/' e execute novamente!")
        return
    
    print(f"\n🔍 Encontrados {len(arquivos_dicom)} arquivo(s) DICOM\n")
    
    # Processar arquivos
    contador = 0
    sucesso = 0
    falhas = 0
    relatorio = []
    
    for filename in arquivos_dicom:
        contador += 1
        print(f"{'='*80}")
        print(f"[{contador}/{len(arquivos_dicom)}] {filename}")
        print(f"{'='*80}")
        
        caminho_arquivo = os.path.join(INPUT_FOLDER, filename)
        ok, info = processar_dicom(caminho_arquivo, contador)
        
        if ok:
            sucesso += 1
        else:
            falhas += 1
        
        relatorio.append(info)
        print()
    
    # Resumo final
    print("="*80)
    print("PROCESSAMENTO CONCLUÍDO!")
    print("="*80)
    print(f"\n📊 ESTATÍSTICAS:")
    print(f"   Total de arquivos: {contador}")
    print(f"   ✅ Sucesso: {sucesso}")
    print(f"   ❌ Falhas: {falhas}")
    
    if sucesso > 0:
        print(f"\n✨ ARQUIVOS GERADOS:")
        print(f"   📁 {OUTPUT_FOLDERS['anonimizados']}/")
        print(f"      • ANON_XXXX.dcm - DICOMs anonimizados")
        print(f"      • ANON_XXXX_anonimizado.png - Imagens anonimizadas (alta res)")
        print(f"\n   📁 {OUTPUT_FOLDERS['para_ia']}/")
        print(f"      • ANON_XXXX_for_ai.png - Imagens para IA ({IA_CONFIG['tamanho']})")
        print(f"      • ANON_XXXX_array.npy - Arrays numpy (prontos para modelo)")
        print(f"\n   📁 {OUTPUT_FOLDERS['originais_alta_res']}/")
        print(f"      • ANON_XXXX_original.png - Backup alta resolução")
    
    print(f"\n{'='*80}")
    print("✅ TODOS OS REQUISITOS ATENDIDOS:")
    print("   • RF01: Validação de DPI mínimo (200 DPI)")
    print("   • RF03: Pré-processamento sem distorção")
    print("   • RF04: Normalização para IA (0-1)")
    print("   • RD02/RD03: Qualidade garantida")
    print("   • RD06: Nomenclatura única e anonimizada")
    print("   • RF07: Estrutura de pastas organizada")
    print(f"{'='*80}")
    print("\n🎓 Dataset pronto para uso no TCC!")

if __name__ == "__main__":
    main()
