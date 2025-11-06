# ml-accessibility
Machine Learning project for automatic web accessibility evaluation (DTM Unibo)
## 🚀 Quick start

To test the baseline script (no Machine Learning yet):

```bash
python src/app/predict_page.py --url "https://www.unibo.it"
```

The script will:
- download the HTML of the page
- evaluate images, text readability, and links using simple rules
- print a JSON accessibility report with a final compliance rating

Example output:
- **Compliant**
- **Partially compliant**
- **Non-compliant**

---

## 🧩 Next steps
1. Fill the CSV files inside `data/processed/` with a few examples.
2. Train the CNN and NLP modules inside the `notebooks/` folder.
3. Compare the ML results with this baseline.
4. Generate the final accessibility report for the paper.
