#  Business Understanding

## Project Title  
**AccessClue**  
Automatic accessibility evaluation system using Machine Learning

---

## Background and Motivation  
Web accessibility has become a key requirement under the **WCAG 2.1** guidelines and the **European Accessibility Act (EAA)**, which both promote inclusion and equal digital access for all users.

Current accessibility checkers generally only determine whether a website is *compliant* or *non-compliant*, without providing deeper insights.  

**AccessClue** aims to go beyond this binary evaluation by developing a system based on **Machine Learning (ML)** models capable of:
- assessing the overall level of accessibility compliance,  
- assigning a score that indicates how far the website is from meeting accessibility standards,  
- and offering practical suggestions to improve it.  

In this way, the system becomes not just a tool for assessment, but a true **operational aid** — helping users understand how much work is needed and what actions are required to achieve full compliance.

---

## Business Objectives  
Develop a prototype that, given a webpage as input, automatically analyses:

1. **Images** → classify as *decorative* or *informative* to verify whether an alternative text (`alt`) is required.  
2. **Texts** → estimate the *readability level* (*easy / medium / difficult*).  
3. **Links** → classify as *descriptive* or *generic* (“click here”, “read more”, etc.).  

Each module will contribute to a **global accessibility score** and a qualitative evaluation (*Compliant / Partially compliant / Non-compliant*).

---

## Success Criteria (SMART Metrics)

| Module | Metric | Target |
|:--------|:--------|:--------|
| **Texts** | Macro-F1 | ≥ 0.70 |
| **Links** | F1 (descriptive class) | ≥ 0.80 |
| **Images** | F1 (informative class) | ≥ 0.80 |

Performance will be measured on a **held-out test set** using **stratified train/test split**.

---

## Risks and Assumptions  
- Dataset size may be small, requiring careful validation.  
- Subjectivity in manual labelling (especially text readability).  
- Bias due to sampling limited websites or image domains.  
- Limited availability of labelled accessibility datasets online.  

---

## Expected Benefits  
- Prototype of a unified accessibility assessment system integrating **Computer Vision** and **NLP**.  
- Structured comparison between **heuristic** and **data-driven** methods.  
- Foundation for future automation of **WCAG-based web auditing tools**.  

---

 *AccessClue — Machine Learning project for automatic web accessibility evaluation (DTM Unibo)*  
