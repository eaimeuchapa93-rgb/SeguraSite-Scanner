import customtkinter as ctk
from tkinter import messagebox
import requests
from bs4 import BeautifulSoup
import threading
import webbrowser
import os
from datetime import datetime
from urllib.parse import urljoin
from collections import deque
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from PIL import Image  # Para logo

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SeguraSitePro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🔒 SeguraSite Pro Free - v0.7")
        self.geometry("1100x800")
        self.resizable(False, False)

        # Header profissional
        header = ctk.CTkFrame(self, height=100, fg_color="#0a0a0a")
        header.pack(fill="x")
        # Logo (baixe um escudo azul e salve como logo.png na pasta)
        try:
            self.logo_image = ctk.CTkImage(light_image=Image.open("logo.png"), size=(80, 80))
            ctk.CTkLabel(header, image=self.logo_image, text="").place(relx=0.02, rely=0.5, anchor="w")
        except:
            pass  # Se não achar logo, ignora
        ctk.CTkLabel(header, text="SeguraSite Pro", font=ctk.CTkFont(size=38, weight="bold"), text_color="#00ccff").place(relx=0.1, rely=0.5, anchor="w")
        ctk.CTkLabel(header, text="Scanner de Vulnerabilidades Profissional • 100% Grátis • Open Source", font=ctk.CTkFont(size=14), text_color="#888").place(relx=0.02, rely=0.85, anchor="w")

        # Tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        self.tab_scan = self.tabview.add("Escanear")
        self.tab_result = self.tabview.add("Resultados")
        self.tab_sobre = self.tabview.add("Sobre")

        self.setup_scan_tab()
        self.setup_result_tab()
        self.setup_sobre_tab()

        self.footer = ctk.CTkLabel(self, text="Versão 0.7 • Uso ético obrigatório", font=ctk.CTkFont(size=12), text_color="#444")
        self.footer.pack(pady=8)

    def setup_scan_tab(self):
        frame = ctk.CTkFrame(self.tab_scan)
        frame.pack(pady=30, padx=40, fill="both", expand=True)

        ctk.CTkLabel(frame, text="Digite a URL do site:", font=ctk.CTkFont(size=18)).pack(pady=10)
        self.url_entry = ctk.CTkEntry(frame, placeholder_text="https://seusite.com.br", width=850, height=45, font=ctk.CTkFont(size=15))
        self.url_entry.pack(pady=10)

        self.confirm_check = ctk.CTkCheckBox(frame, text="Confirmo que este site é meu ou tenho autorização para testar", font=ctk.CTkFont(size=14))
        self.confirm_check.pack(pady=10)

        ctk.CTkLabel(frame, text="Tipo de escaneamento:", font=ctk.CTkFont(size=16)).pack(pady=(20,5))
        self.scan_mode = ctk.CTkSegmentedButton(frame, values=["Rápido (1 página)", "Completo (até 10 páginas)"], font=ctk.CTkFont(size=14))
        self.scan_mode.set("Rápido (1 página)")
        self.scan_mode.pack(pady=5)

        self.status_label = ctk.CTkLabel(frame, text="Pronto para escanear", font=ctk.CTkFont(size=15), text_color="#00ff88")
        self.status_label.pack(pady=15)

        self.progress = ctk.CTkProgressBar(frame, width=850, height=15)
        self.progress.pack(pady=10)
        self.progress.set(0)

        self.scan_btn = ctk.CTkButton(frame, text="🚀 INICIAR ESCANEAMENTO PRO", font=ctk.CTkFont(size=18, weight="bold"), height=60,
                                      command=self.start_scan)
        self.scan_btn.pack(pady=20)

    def setup_result_tab(self):
        self.result_text = ctk.CTkTextbox(self.tab_result, font=ctk.CTkFont(size=14))
        self.result_text.pack(fill="both", expand=True, padx=20, pady=20)

        btn_frame = ctk.CTkFrame(self.tab_result)
        btn_frame.pack(pady=15)
        self.btn_report_html = ctk.CTkButton(btn_frame, text="📄 ABRIR RELATÓRIO HTML", height=50,
                                             font=ctk.CTkFont(size=16, weight="bold"), state="disabled", command=self.open_report_html)
        self.btn_report_html.pack(side="left", padx=10)
        self.btn_report_pdf = ctk.CTkButton(btn_frame, text="📤 EXPORTAR PDF", height=50,
                                            font=ctk.CTkFont(size=16, weight="bold"), state="disabled", command=self.export_pdf)
        self.btn_report_pdf.pack(side="left", padx=10)

    def setup_sobre_tab(self):
        texto = "SeguraSite Pro Free v0.7\n\nFerramenta profissional gratuita para análise de vulnerabilidades web.\n\nUso restrito a sites autorizados. Responsabilidade do usuário.\n\nVersão open-source para a comunidade de segurança."
        ctk.CTkLabel(self.tab_sobre, text=texto, font=ctk.CTkFont(size=16), justify="center").pack(pady=80)

    def update_status(self, texto, progress=0, color="#00ff88"):
        self.status_label.configure(text=texto, text_color=color)
        self.progress.set(progress)
        self.update()

    def log_result(self, texto):
        self.result_text.insert("end", texto + "\n")
        self.result_text.see("end")
        self.update()

    def start_scan(self):
        if not self.confirm_check.get():
            messagebox.showerror("Aviso", "Confirme que você tem autorização antes de prosseguir!")
            return

        url = self.url_entry.get().strip()
        if not url.startswith("http"):
            messagebox.showerror("Erro", "URL inválida! Use https://")
            return

        self.scan_btn.configure(state="disabled", text="🔄 ESCANEANDO...")
        self.result_text.delete("1.0", "end")
        self.btn_report_html.configure(state="disabled")
        self.btn_report_pdf.configure(state="disabled")

        threading.Thread(target=self.run_scan, args=(url,), daemon=True).start()

    def run_scan(self, base_url):
        findings = []
        max_pages = 10 if self.scan_mode.get() == "Completo (até 10 páginas)" else 1
        self.update_status("Iniciando scan pro...", 0.05)

        try:
            visited = set()
            queue = deque([base_url])
            pages_scanned = 0

            while queue and pages_scanned < max_pages:
                url = queue.popleft()
                if url in visited: continue
                visited.add(url)

                self.update_status(f"🔍 Escaneando página {pages_scanned+1}/{max_pages}: {url[-40:]}...", 0.05 + (pages_scanned/max_pages)*0.6)

                try:
                    r = requests.get(url, timeout=12, headers={"User-Agent": "SeguraSite-Pro/0.7"})
                    soup = BeautifulSoup(r.text, 'html.parser')

                    # Headers
                    for header, info in [
                        ("X-Frame-Options", ("Alta", "Clickjacking", "Adicione X-Frame-Options: DENY no servidor")),
                        ("Content-Security-Policy", ("Crítica", "XSS/injeções", "Implemente CSP completo")),
                        ("Strict-Transport-Security", ("Alta", "Downgrade HTTPS", "Ative HSTS com max-age=31536000")),
                        ("X-Content-Type-Options", ("Média", "MIME sniffing", "Adicione X-Content-Type-Options: nosniff"))
                    ]:
                        if header not in r.headers:
                            findings.append({
                                "vuln": header,
                                "severity": info[0],
                                "desc": info[1],
                                "fix": info[2],
                                "page": url.replace(base_url, "") or "/",
                                "full_url": url
                            })

                    # Formulários para SQLi e XSS
                    forms = soup.find_all("form")
                    if forms:
                        self.update_status("🛡️ Testando SQL Injection e XSS nos formulários...", (pages_scanned + 0.5)/max_pages)
                        for form in forms[:3]:  # Limita pra não abusar
                            action = urljoin(url, form.get("action", ""))
                            method = form.get("method", "get").lower()
                            inputs = [i.get("name") for i in form.find_all("input") if i.get("name")]

                            if inputs:
                                # SQLi payload
                                sql_payload = {inp: "' OR 1=1 --" for inp in inputs}
                                try:
                                    if method == "post":
                                        res = requests.post(action, data=sql_payload, timeout=8)
                                    else:
                                        res = requests.get(action, params=sql_payload, timeout=8)

                                    if "syntax" in res.text.lower() or "sql" in res.text.lower() or "error" in res.text.lower():
                                        findings.append({
                                            "vuln": "SQL Injection possível",
                                            "severity": "Crítica",
                                            "desc": "Resposta indica erro SQL",
                                            "fix": "Use prepared statements e valide entradas",
                                            "page": url.replace(base_url, "") or "/",
                                            "full_url": url
                                        })
                                        self.log_result("⚠️ SQLi detectado em formulário!")
                                except:
                                    pass

                                # XSS payload
                                xss_payloads = ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>", "';alert(1);//"]
                                for xss in xss_payloads:
                                    xss_pay = {inp: xss for inp in inputs}
                                    try:
                                        if method == "post":
                                            res_xss = requests.post(action, data=xss_pay, timeout=8)
                                        else:
                                            res_xss = requests.get(action, params=xss_pay, timeout=8)

                                        if xss in res_xss.text or "alert(1)" in res_xss.text:
                                            findings.append({
                                                "vuln": "XSS possível",
                                                "severity": "Crítica",
                                                "desc": "Payload refletido na resposta",
                                                "fix": "Escape/sanitize saídas HTML e use CSP",
                                                "page": url.replace(base_url, "") or "/",
                                                "full_url": url
                                            })
                                            self.log_result("⚠️ XSS detectado em formulário!")
                                            break  # Para não repetir se achar um
                                    except:
                                        pass

                    # Crawler
                    for a in soup.find_all("a", href=True):
                        full = urljoin(url, a["href"])
                        if base_url in full and full not in visited and len(visited) < max_pages + 5:
                            queue.append(full)

                    pages_scanned += 1
                except:
                    pass

            self.update_status("📄 Gerando relatório pro...", 0.95)
            self.generate_reports(base_url, findings)
            self.btn_report_html.configure(state="normal")
            self.btn_report_pdf.configure(state="normal")
            self.update_status("✅ Scan finalizado!", 1.0, "#00ff88")
            self.log_result("🎉 Scan Pro Finalizado!\nRelatórios prontos.")

        except Exception as e:
            self.log_result(f"❌ Erro: {str(e)}")
            self.update_status("Erro no scan", 0, "#ff4444")
        finally:
            self.scan_btn.configure(state="normal", text="🚀 INICIAR ESCANEAMENTO PRO")

    def generate_reports(self, base_url, findings):
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        severity_color = {"Crítica": "#ff3366", "Alta": "#ff8833", "Média": "#ffcc00", "Baixa": "#00cc66"}

        # HTML com links clicáveis
        html = f"""<html><head><meta charset="utf-8"><title>Relatório SeguraSite Pro - {base_url}</title>
        <style>body{{background:#0f0f0f;color:#ddd;font-family:Arial;padding:40px;}} 
        h1{{color:#00ccff;}} table{{width:100%;border-collapse:collapse;margin:20px 0;}}
        th,td{{padding:12px;text-align:left;border-bottom:1px solid #333;}} th{{background:#1a1a1a;}}
        a{{color:#00ccff;text-decoration:none;}} a:hover{{text-decoration:underline;}}
        .crit{{color:#ff3366;font-weight:bold;}} .alta{{color:#ff8833;}} .media{{color:#ffcc00;}} .baixa{{color:#00cc66;}}</style></head><body>
        <h1>🔒 Relatório SeguraSite Pro Free v0.7</h1>
        <p>Site: {base_url} | Data: {agora} | Páginas: {len(set(f['page'] for f in findings))}</p>
        <h2>🔍 Vulnerabilidades</h2><table><tr><th>Vuln</th><th>Severidade</th><th>Onde</th><th>Como Corrigir</th></tr>"""
        for f in findings:
            cl = {"Crítica":"crit", "Alta":"alta", "Média":"media", "Baixa":"baixa"}.get(f["severity"], "media")
            onde_link = f'<a href="{f["full_url"]}">{f["page"]}</a>'
            html += f'<tr><td>{f["vuln"]}</td><td class="{cl}">{f["severity"]} ({f["desc"]})</td><td>{onde_link}</td><td>{f["fix"]}</td></tr>'
        html += "</table><p>Uso ético: Compartilhe este relatório apenas com responsáveis. Testes apenas em sites autorizados.</p></body></html>"

        with open("relatorio_pro.html", "w", encoding="utf-8") as f:
            f.write(html)
        self.html_path = os.path.abspath("relatorio_pro.html")

        # PDF com hiperlinks (simples sobreposição)
        pdf_name = "relatorio_pro.pdf"
        doc = SimpleDocTemplate(pdf_name, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Relatório SeguraSite Pro Free v0.7", styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Site: {base_url}", styles['Normal']))
        elements.append(Paragraph(f"Data: {agora}", styles['Normal']))
        elements.append(Spacer(1, 24))

        data = [["Vulnerabilidade", "Severidade", "Onde", "Como Corrigir"]]
        for f in findings:
            data.append([f["vuln"], f["severity"] + " (" + f["desc"] + ")", f["page"], f["fix"]])

        t = Table(data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        elements.append(t)

        doc.build(elements)
        self.pdf_path = os.path.abspath(pdf_name)

    def open_report_html(self):
        webbrowser.open(f"file://{self.html_path}")

    def export_pdf(self):
        os.startfile(self.pdf_path)  # Abre o PDF no leitor padrão

if __name__ == "__main__":
    app = SeguraSitePro()
    app.mainloop()