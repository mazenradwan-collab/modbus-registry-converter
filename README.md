# Modbus Registry Map Converter

برنامج لتحويل ملفات Modbus Registry Map من صيغ مختلفة (CSV, Excel, PDF) إلى صيغة موحدة.

## الميزات

✅ قراءة ملفات CSV و Excel و PDF
✅ استخراج معلومات السجل تلقائياً
✅ تحويل إلى صيغة موحدة
✅ معالجة أنواع بيانات متعددة
✅ واجهة سطر أوامر سهلة الاستخدام

## المتطلبات

- Python 3.8+
- المكتبات المذكورة في `requirements.txt`

## التثبيت

```bash
# استنساخ المستودع
git clone https://github.com/mazenradwan-collab/modbus-registry-converter.git
cd modbus-registry-converter

# تثبيت المكتبات
pip install -r requirements.txt
```

## الاستخدام

### الطريقة البسيطة:
```bash
python main.py --input input.csv --output output.csv
python main.py --input data.xlsx --output output.csv
python main.py --input registers.pdf --output output.csv
```

### الخيارات المتقدمة:
```bash
python main.py --input file.csv --output result.csv --format excel
python main.py --input file.csv --output result.csv --validate
```

## صيغة الإخراج الموحدة

```
RegisterName,DisplayName,FunctionCode,RegisterType,Address,DataType,RegisterCount,ScaleFactor,Unit,Access,Polling_ms,Enabled
```

### شرح الحقول:
- **RegisterName**: اسم السجل الفريد
- **DisplayName**: اسم العرض (يظهر للمستخدم)
- **FunctionCode**: رمز الدالة Modbus (1-4, 16, 23)
- **RegisterType**: نوع السجل (Coil, Discrete Input, Input Register, Holding Register)
- **Address**: عنوان السجل
- **DataType**: نوع البيانات (INT16, INT32, FLOAT32, FLOAT64, STRING)
- **RegisterCount**: عدد السجلات
- **ScaleFactor**: معامل التحجيم
- **Unit**: الوحدة
- **Access**: نوع الوصول (Read, Write, Read/Write)
- **Polling_ms**: فترة الاستطلاع بالميلي ثانية
- **Enabled**: تفعيل/تعطيل السجل (True/False)

## التطوير

```bash
# تشغيل الاختبارات
python -m pytest tests/

# تشغيل التحقق من الكود
flake8 .
black .
```

## المساهمة

يرحب المشروع بالمساهمات! يرجى:
1. عمل Fork للمشروع
2. إنشاء فرع للميزة الجديدة
3. الالتزام بالتغييرات
4. دفع إلى الفرع
5. فتح Pull Request

## الترخيص

MIT License

## الدعم

للمساعدة والأسئلة، يرجى فتح Issue في المستودع.
