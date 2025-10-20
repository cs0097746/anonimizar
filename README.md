# ⚡ ANONIMIZADOR DE ECGs - HUSM

## 🎯 **Sistema Automático de Anonimização**

Processa arquivos DICOM do HUSM:
- Extrai PDF embutido
- Converte para PNG
- Anonimiza metadados e imagem
- Oculta dados sensíveis (ID, Nome, etc.)
- Preserva gráfico do ECG

---

## 🚀 **COMO USAR:**

### **Passo 1:**
Coloque seus arquivos `.dcm` em:
```
pasta_com_dicoms/
```

### **Passo 2:**
Execute:
```bash
python processar_tudo.py
```

### **Passo 3:**
Pronto! Veja resultado em:
```
ecgs_anonimizados/
├── anonimizado_0001.dcm  ← Metadados anonimizados
├── anonimizado_0001.png  ← Imagem anonimizada
└── ...
```

---

## 📊 **Resultado:**

**Área com dados sensíveis:** ⬛ PRETA (canto superior esquerdo)  
- Oculta: ID, Nome, Sexo, Pressão, Técnico, Médico, etc.

**Dados preservados:** ✅ VISÍVEIS
- Gráfico ECG completo (12 derivações)
- HR, Pd, PR, QRS, QT/QTC, etc.
- Resultado do diagnóstico

---

## ⚙️ **Ajustar área ocultada:**

Edite `processar_tudo.py` linha 98:
```python
largura_percentual=0.20  # 20% da largura (ajustável)
altura_percentual=0.25   # 25% da altura (ajustável)
```

---

## 🔒 **Conformidade LGPD:**

✅ PatientID anonimizado  
✅ PatientName anonimizado  
✅ Datas alteradas  
✅ Dados visuais ocultados  
✅ Informações médicas preservadas  

---

**Sistema completo e funcional! 🎓**
