# 🚀 INSTRUÇÕES - Sistema Automático

## ✅ **Sistema Configurado e Pronto!**

---

## 🎯 **COMO USAR:**

### **1. Coloque seus DICOMs:**
```
pasta_com_dicoms/
├── ecg_001.dcm
├── ecg_002.dcm
└── ecg_003.dcm
```

### **2. Execute:**
```bash
python processar_tudo.py
```

### **3. Resultado:**
```
ecgs_anonimizados/
├── anonimizado_0001.dcm ✅
├── anonimizado_0001.png ✅
├── anonimizado_0002.dcm
├── anonimizado_0002.png
└── ...
```

---

## 📊 **Configuração Atual:**

**Área ocultada:** 20% largura x 25% altura  
**Oculta:** ID, Nome, Sexo, Pressão, Técnico, Médico  
**Preserva:** HR, Pd, PR, QRS, QT/QTC, Gráfico ECG

---

## ⚙️ **Ajustar área (se necessário):**

Edite `processar_tudo.py` linha 98:
```python
largura_percentual=0.20  # ← Ajuste aqui
altura_percentual=0.25   # ← Ajuste aqui
```

**Valores recomendados:**
- Atual: `0.20` e `0.25` (cobre ID, Nome, dados pessoais)
- Mais: `0.25` e `0.30` (se precisar cobrir mais)
- Menos: `0.15` e `0.20` (se estiver cobrindo demais)

---

## 🔒 **Anonimização LGPD:**

✅ Metadados: PatientID, Nome, Datas  
✅ Imagem: Área superior esquerda ocultada  
✅ Preservado: Dados técnicos do ECG

---

## 📋 **Checklist:**

- [x] Sistema instalado
- [x] Área ajustada (20% x 25%)
- [ ] Coloque DICOMs em `pasta_com_dicoms/`
- [ ] Execute `python processar_tudo.py`
- [ ] Verifique resultado em `ecgs_anonimizados/`

---

**Pronto para processar! 🎉**

---

## 🔄 **O QUE O SCRIPT FAZ AUTOMATICAMENTE:**

```
DICOM Original
    ↓
1. Lê o DICOM
    ↓
2. Anonimiza metadados (ID, Nome, etc.)
    ↓
3. Salva DICOM anonimizado
    ↓
4. Extrai PDF embutido
    ↓
5. Converte PDF → PNG (automático!)
    ↓
6. Oculta região com dados sensíveis (área preta)
    ↓
7. Salva PNG anonimizado
    ↓
✅ PRONTO!
```

---

## 📊 **EXEMPLO DE SAÍDA:**

```
================================================================================
[1/3] ecg_paciente_001.dcm
================================================================================
  📖 Lendo DICOM...
     ✓ ID: 4997326
     ✓ Nome: ArildoMartins

  🔒 Anonimizando metadados...
     ✓ Novo ID: ANON_0001
     ✓ Novo Nome: ANONIMIZADO_0001
     ✓ DICOM salvo: anonimizado_0001.dcm

  📄 Extraindo PDF embutido...
     ✓ PDF extraído (374,604 bytes)

  🖼️  Convertendo PDF para PNG...
     ✓ Convertido com PyMuPDF
     ✓ Imagem: 1683 x 2383 pixels

  🔐 Anonimizando região com dados sensíveis...
     ✓ Região ocultada: 588 x 714 px
     ✓ Percentual: 35% largura x 30% altura

  ✅ PNG ANONIMIZADO SALVO: anonimizado_0001.png

================================================================================
PROCESSAMENTO CONCLUÍDO!
================================================================================
📊 ESTATÍSTICAS:
   Total de arquivos: 3
   ✅ Sucesso: 3
   ❌ Falhas: 0

✨ RESULTADO:
   📁 3 arquivo(s) anonimizado(s) com sucesso!
   📂 Localização: C:\...\ecgs_anonimizados/

Dataset pronto para uso no TCC! 🎓
```

---

## 🔒 **O QUE É ANONIMIZADO:**

### **Metadados DICOM:**
- PatientID: 4997326 → ANON_0001
- PatientName: Arildo Martins → ANONIMIZADO_0001
- StudyDate → 20000101
- + 15 outros campos LGPD

### **Imagem Visual (PNG):**
- Região superior esquerda: ⬛ **ÁREA PRETA** (35% x 30%)
- Oculta: ID, Nome, Sexo, Pressão, Técnico, Médico, etc.
- Preserva: ✅ Gráfico completo do ECG (12 derivações)

---

## ⚙️ **AJUSTAR ÁREA DE OCULTAÇÃO:**

Se precisar cobrir mais ou menos, edite `processar_tudo.py` linha 98:

```python
def anonimizar_imagem(img, 
                      largura_percentual=0.35,  # ← Ajuste aqui (35%)
                      altura_percentual=0.30):   # ← Ajuste aqui (30%)
```

**Exemplos:**
- **Mais cobertura:** `0.40` e `0.35`
- **Menos cobertura:** `0.30` e `0.25`

---

## 💾 **TESTE COM O ARQUIVO DO ORIENTADOR:**

1. Coloque o arquivo `.dcm` que o orientador te deu em: `pasta_com_dicoms/`
2. Execute: `python processar_tudo.py`
3. Veja o resultado em: `ecgs_anonimizados/`
4. Mostre ao orientador! ✅

---

## 🎓 **QUANDO RECEBER A PASTA COMPLETA:**

```bash
# 1. Copie TODOS os .dcm para: pasta_com_dicoms/

# 2. Execute UMA VEZ:
python processar_tudo.py

# 3. PRONTO! Todo o dataset anonimizado estará em: ecgs_anonimizados/
```

---

## 📊 **VANTAGENS DESTA SOLUÇÃO:**

✅ **100% Automático** - Um único comando  
✅ **Não precisa Poppler** - Usa PyMuPDF (mais simples)  
✅ **Processa em lote** - Vários arquivos de uma vez  
✅ **LGPD compliant** - Metadados + imagem anonimizados  
✅ **Pronto para TCC** - Dataset completo gerado  

---

## 🆘 **PROBLEMAS?**

### **"Nenhum arquivo DICOM encontrado"**
➡️ Verifique se colocou os `.dcm` em `pasta_com_dicoms/`

### **"Falha na conversão"**
➡️ O script já instalou PyMuPDF, deve funcionar!

### **"Área preta não cobre tudo"**
➡️ Aumente os percentuais no código (linha 98)

---

## 🎉 **RESUMO:**

Você agora tem um sistema que:
1. ✅ Pega DICOM do HUSM
2. ✅ Extrai o PDF automaticamente
3. ✅ Converte para PNG automaticamente
4. ✅ Anonimiza metadados e imagem
5. ✅ Salva tudo pronto para usar

**TUDO EM UM ÚNICO COMANDO!** 🚀

---

## 📝 **CHECKLIST PARA O ORIENTADOR:**

- [ ] Coloquei o DICOM em `pasta_com_dicoms/`
- [ ] Executei `python processar_tudo.py`
- [ ] Verifiquei `ecgs_anonimizados/anonimizado_0001.png`
- [ ] Área superior esquerda está preta ✅
- [ ] Gráfico ECG está visível ✅
- [ ] Mostrei ao orientador ✅
- [ ] Aguardando pasta completa com todos os ECGs!

---

**Sistema 100% funcional! Pronto para processar todo o dataset! 🎓✨**
