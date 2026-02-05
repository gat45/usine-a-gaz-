import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
import subprocess
import psutil
import json
import os
from datetime import datetime
import webbrowser
import httpx
from pathlib import Path

class HX365TkinterGUI:
    """
    Interface Tkinter pour le HX365 Command Center
    Permet de lancer le chatbot, surveiller l'état des services
    et gérer les fonctionnalités du système
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.setup_variables()
        self.setup_styles()
        self.create_widgets()
        self.setup_bindings()
        self.update_system_stats()
        
    def setup_window(self):
        """Configuration de la fenêtre principale"""
        self.root.title("HX365 Command Center - Interface Tkinter")
        self.root.geometry("1200x800")
        self.root.configure(bg='#0a0a0f')
        
        # Rendre la fenêtre redimensionnable
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Centrer la fenêtre
        self.center_window()
        
    def center_window(self):
        """Centre la fenêtre sur l'écran"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def setup_variables(self):
        """Configuration des variables d'état"""
        self.fastflowlm_status = tk.StringVar(value="Arrêté")
        self.companion_status = tk.StringVar(value="Arrêté")
        self.rag_status = tk.StringVar(value="Inactif")
        self.agent_status = tk.StringVar(value="Inactif")
        
        self.fastflowlm_process = None
        self.companion_process = None
        
        # Variables pour les statistiques système
        self.cpu_var = tk.StringVar(value="CPU: 0%")
        self.ram_var = tk.StringVar(value="RAM: 0GB")
        self.npu_var = tk.StringVar(value="NPU: 0%")
        
    def setup_styles(self):
        """Configuration des styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Couleurs personnalisées
        style.configure('Dark.TFrame', background='#0a0a0f')
        style.configure('Dark.TLabel', background='#0a0a0f', foreground='#e2e8f0')
        style.configure('Dark.TButton', background='#0ea5e9', foreground='#ffffff')
        style.configure('Status.TLabel', background='#0a0a0f', foreground='#10b981')
        
    def create_widgets(self):
        """Création des widgets de l'interface"""
        # Frame principale
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Header
        header_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        header_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        
        title_label = ttk.Label(header_frame, text="HX365 Command Center", 
                               font=('Arial', 16, 'bold'), style='Dark.TLabel')
        title_label.grid(row=0, column=0, sticky='w')
        
        subtitle_label = ttk.Label(header_frame, text="Interface de Contrôle Système", 
                                  font=('Arial', 10), style='Dark.TLabel')
        subtitle_label.grid(row=1, column=0, sticky='w')
        
        # Boutons de contrôle
        control_frame = ttk.Frame(header_frame, style='Dark.TFrame')
        control_frame.grid(row=0, column=1, rowspan=2, sticky='e')
        
        ttk.Button(control_frame, text="Lancer Chatbot", 
                  command=self.launch_chatbot, style='Dark.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Lancer FastFlowLM", 
                  command=self.launch_fastflowlm, style='Dark.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Lancer Companion", 
                  command=self.launch_companion, style='Dark.TButton').pack(side=tk.LEFT, padx=5)
        
        # Panneau gauche - Contrôles et états
        left_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        left_frame.grid(row=1, column=0, sticky='ns', padx=(0, 10))
        left_frame.rowconfigure(4, weight=1)
        
        # États des services
        status_frame = ttk.LabelFrame(left_frame, text="États des Services", style='Dark.TFrame')
        status_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(status_frame, text="FastFlowLM:", style='Dark.TLabel').pack(anchor='w')
        self.fflm_status_label = ttk.Label(status_frame, textvariable=self.fastflowlm_status, 
                                          style='Status.TLabel')
        self.fflm_status_label.pack(anchor='w', padx=(20, 0))
        
        ttk.Label(status_frame, text="Companion:", style='Dark.TLabel').pack(anchor='w', pady=(5, 0))
        self.comp_status_label = ttk.Label(status_frame, textvariable=self.companion_status, 
                                          style='Status.TLabel')
        self.comp_status_label.pack(anchor='w', padx=(20, 0))
        
        ttk.Label(status_frame, text="RAG:", style='Dark.TLabel').pack(anchor='w', pady=(5, 0))
        self.rag_status_label = ttk.Label(status_frame, textvariable=self.rag_status, 
                                         style='Status.TLabel')
        self.rag_status_label.pack(anchor='w', padx=(20, 0))
        
        ttk.Label(status_frame, text="Agent:", style='Dark.TLabel').pack(anchor='w', pady=(5, 0))
        self.agent_status_label = ttk.Label(status_frame, textvariable=self.agent_status, 
                                           style='Status.TLabel')
        self.agent_status_label.pack(anchor='w', padx=(20, 0))
        
        # Contrôles RAG
        rag_frame = ttk.LabelFrame(left_frame, text="Contrôles RAG", style='Dark.TFrame')
        rag_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(rag_frame, text="Charger Document", 
                  command=self.load_document, style='Dark.TButton').pack(fill='x', pady=2)
        ttk.Button(rag_frame, text="Rechercher", 
                  command=self.search_rag, style='Dark.TButton').pack(fill='x', pady=2)
        ttk.Button(rag_frame, text="Indexer", 
                  command=self.index_rag, style='Dark.TButton').pack(fill='x', pady=2)
        
        # Contrôles Agents
        agent_frame = ttk.LabelFrame(left_frame, text="Contrôles Agents", style='Dark.TFrame')
        agent_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(agent_frame, text="Lister Agents", 
                  command=self.list_agents, style='Dark.TButton').pack(fill='x', pady=2)
        ttk.Button(agent_frame, text="Exécuter Agent", 
                  command=self.run_agent, style='Dark.TButton').pack(fill='x', pady=2)
        
        # Contrôles de session
        session_frame = ttk.LabelFrame(left_frame, text="Contrôles Session", style='Dark.TFrame')
        session_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(session_frame, text="Nouvelle Session", 
                  command=self.new_session, style='Dark.TButton').pack(fill='x', pady=2)
        ttk.Button(session_frame, text="Réinitialiser", 
                  command=self.reset_session, style='Dark.TButton').pack(fill='x', pady=2)
        ttk.Button(session_frame, text="Exporter", 
                  command=self.export_session, style='Dark.TButton').pack(fill='x', pady=2)
        
        # Statistiques système
        stats_frame = ttk.LabelFrame(left_frame, text="Statistiques Système", style='Dark.TFrame')
        stats_frame.pack(fill='x', pady=(0, 10))
        
        self.cpu_label = ttk.Label(stats_frame, textvariable=self.cpu_var, style='Dark.TLabel')
        self.cpu_label.pack(anchor='w')
        
        self.ram_label = ttk.Label(stats_frame, textvariable=self.ram_var, style='Dark.TLabel')
        self.ram_label.pack(anchor='w')
        
        self.npu_label = ttk.Label(stats_frame, textvariable=self.npu_var, style='Dark.TLabel')
        self.npu_label.pack(anchor='w')
        
        # Boutons de gestion
        management_frame = ttk.LabelFrame(left_frame, text="Gestion Système", style='Dark.TFrame')
        management_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(management_frame, text="Redémarrer NPU", 
                  command=self.restart_npu, style='Dark.TButton').pack(fill='x', pady=2)
        ttk.Button(management_frame, text="Nettoyer Cache", 
                  command=self.clear_cache, style='Dark.TButton').pack(fill='x', pady=2)
        ttk.Button(management_frame, text="Générer Rapport", 
                  command=self.generate_report, style='Dark.TButton').pack(fill='x', pady=2)
        
        # Panneau droit - Chat et logs
        right_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        right_frame.grid(row=1, column=1, sticky='nsew')
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Zone de chat
        chat_frame = ttk.LabelFrame(right_frame, text="Interface Chat", style='Dark.TFrame')
        chat_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        chat_frame.columnconfigure(0, weight=1)
        
        # Zone de messages
        self.chat_display = scrolledtext.ScrolledText(chat_frame, height=10, 
                                                     bg='#151626', fg='#e2e8f0',
                                                     insertbackground='#e2e8f0',
                                                     font=('Consolas', 10))
        self.chat_display.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Zone de saisie
        input_frame = ttk.Frame(chat_frame, style='Dark.TFrame')
        input_frame.pack(fill='x', padx=5, pady=(0, 5))
        
        self.user_input = tk.Text(input_frame, height=3, bg='#151626', fg='#e2e8f0',
                                 insertbackground='#e2e8f0', font=('Consolas', 10))
        self.user_input.pack(fill='x', side=tk.LEFT, expand=True, padx=(0, 5))
        
        ttk.Button(input_frame, text="Envoyer", command=self.send_message, 
                  style='Dark.TButton').pack(side=tk.RIGHT)
        
        # Onglets pour logs et configuration
        notebook = ttk.Notebook(right_frame)
        notebook.grid(row=1, column=0, sticky='nsew')
        
        # Onglet Logs
        logs_frame = ttk.Frame(notebook, style='Dark.TFrame')
        notebook.add(logs_frame, text='Logs Système')
        
        self.logs_display = scrolledtext.ScrolledText(logs_frame, 
                                                    bg='#151626', fg='#e2e8f0',
                                                    insertbackground='#e2e8f0',
                                                    font=('Consolas', 9))
        self.logs_display.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Onglet Configuration
        config_frame = ttk.Frame(notebook, style='Dark.TFrame')
        notebook.add(config_frame, text='Configuration')
        
        config_scroll = scrolledtext.ScrolledText(config_frame, 
                                                 bg='#151626', fg='#e2e8f0',
                                                 insertbackground='#e2e8f0',
                                                 font=('Consolas', 9))
        config_scroll.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Ajouter du contenu de configuration
        config_content = """
Configuration HX365 Command Center
===================================

Variables d'environnement:
- FASTFLOWLM_BASE: http://127.0.0.1:52625/v1
- COMPANION_BASE: http://127.0.0.1:52626/v1
- EMBEDDING_DIM: 384
- MAX_CONTEXT_LENGTH: 4096
- CHUNK_SIZE: 512

Paramètres du modèle:
- Temperature: 0.7
- Top-P: 0.9
- Max Tokens: 2048
- Presence Penalty: 0.0
- Frequency Penalty: 0.0

Optimisations matérielles:
- CPU Affinity: Activé
- NPU Acceleration: Activé
- GPU Offload: Activé
        """
        config_scroll.insert('1.0', config_content)
        config_scroll.config(state='disabled')
        
        # Ajouter un message de bienvenue
        self.add_to_chat("HX365 Command Center démarré", "system")
        self.add_to_log("Interface Tkinter HX365 démarrée", "info")
        
    def setup_bindings(self):
        """Configuration des événements"""
        self.user_input.bind('<Return>', lambda e: self.send_message())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def add_to_chat(self, message, sender="system"):
        """Ajoute un message à la zone de chat"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = "#10b981" if sender == "system" else "#0ea5e9" if sender == "user" else "#e2e8f0"
        
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.chat_display.insert(tk.END, f"{sender}: ", "sender")
        self.chat_display.insert(tk.END, f"{message}\n", "message")
        
        # Appliquer les couleurs
        self.chat_display.tag_configure("timestamp", foreground="#64748b")
        self.chat_display.tag_configure("sender", foreground=color, font=('Consolas', 10, 'bold'))
        self.chat_display.tag_configure("message", foreground="#e2e8f0")
        
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
        
    def add_to_log(self, message, level="info"):
        """Ajoute un message au journal"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {"info": "#10b981", "warn": "#f59e0b", "error": "#ef4444", "debug": "#8b5cf6"}
        color = colors.get(level, "#e2e8f0")
        
        self.logs_display.config(state='normal')
        self.logs_display.insert(tk.END, f"[{timestamp}] [{level.upper()}] {message}\n", level)
        self.logs_display.tag_configure(level, foreground=color)
        self.logs_display.config(state='disabled')
        self.logs_display.see(tk.END)
        
    def send_message(self):
        """Envoie un message utilisateur"""
        message = self.user_input.get("1.0", tk.END).strip()
        if message:
            self.add_to_chat(message, "user")
            self.user_input.delete("1.0", tk.END)
            
            # Simuler une réponse du système
            self.simulate_response(message)
            
    def simulate_response(self, user_message):
        """Simule une réponse du système"""
        # Ceci est une simulation - dans une implémentation réelle, 
        # cela appellerait l'API FastFlowLM
        response = f"Réponse simulée pour: {user_message[:50]}..."
        self.add_to_chat(response, "assistant")
        self.add_to_log(f"Message envoyé: {user_message[:30]}...", "info")
        
    def launch_chatbot(self):
        """Lance l'interface de chatbot"""
        try:
            # Essayer de lancer le GUI web existant
            webbrowser.open("hx365_gui.html")
            self.add_to_log("Interface web du chatbot ouverte", "info")
        except Exception as e:
            self.add_to_log(f"Erreur lors de l'ouverture de l'interface web: {e}", "error")
            # Si le GUI web n'est pas disponible, ouvrir une fenêtre de chat simple
            self.open_simple_chat()
        
    def open_simple_chat(self):
        """Ouvre une fenêtre de chat simple"""
        chat_window = tk.Toplevel(self.root)
        chat_window.title("Chatbot - Interface Simple")
        chat_window.geometry("800x600")
        chat_window.configure(bg='#0a0a0f')
        
        # Zone de messages
        chat_area = scrolledtext.ScrolledText(chat_window, bg='#151626', fg='#e2e8f0',
                                            insertbackground='#e2e8f0', font=('Consolas', 10))
        chat_area.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Zone d'entrée
        input_frame = ttk.Frame(chat_window, style='Dark.TFrame')
        input_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        input_entry = tk.Entry(input_frame, bg='#151626', fg='#e2e8f0', 
                              insertbackground='#e2e8f0', font=('Consolas', 10))
        input_entry.pack(side=tk.LEFT, fill='x', expand=True, padx=(0, 5))
        
        def send_chat():
            msg = input_entry.get()
            if msg:
                chat_area.insert(tk.END, f"Vous: {msg}\n", "user")
                chat_area.see(tk.END)
                input_entry.delete(0, tk.END)
                
                # Simuler réponse
                chat_area.insert(tk.END, f"Assistant: Réponse à '{msg[:20]}...'\n", "assistant")
                chat_area.see(tk.END)
        
        ttk.Button(input_frame, text="Envoyer", command=send_chat, 
                  style='Dark.TButton').pack(side=tk.RIGHT)
        
        chat_area.tag_configure("user", foreground="#0ea5e9", font=('Consolas', 10, 'bold'))
        chat_area.tag_configure("assistant", foreground="#10b981", font=('Consolas', 10, 'bold'))
        
    def launch_fastflowlm(self):
        """Lance le serveur FastFlowLM"""
        try:
            # Vérifier si le fichier main_final.py existe
            if os.path.exists("main_final.py"):
                self.fastflowlm_process = subprocess.Popen([
                    "python", "main_final.py", "--host", "127.0.0.1", "--port", "8080"
                ])
                self.fastflowlm_status.set("Démarrage...")
                self.add_to_log("Lancement de FastFlowLM...", "info")
                
                # Mettre à jour le statut après un délai
                self.root.after(3000, self.check_fastflowlm_status)
            else:
                messagebox.showerror("Erreur", "Fichier main_final.py non trouvé")
                self.add_to_log("Fichier main_final.py non trouvé", "error")
        except Exception as e:
            self.add_to_log(f"Erreur lors du lancement de FastFlowLM: {e}", "error")
            self.fastflowlm_status.set("Erreur")
    
    def check_fastflowlm_status(self):
        """Vérifie le statut de FastFlowLM"""
        # Dans une implémentation réelle, on vérifierait l'API
        # Pour la simulation, on suppose que c'est prêt
        self.fastflowlm_status.set("Prêt")
        self.add_to_log("FastFlowLM est prêt", "info")
    
    def launch_companion(self):
        """Lance le serveur Companion"""
        try:
            # Simuler le lancement du Companion
            self.companion_status.set("Démarrage...")
            self.add_to_log("Lancement du Companion...", "info")
            
            # Simuler le démarrage
            self.root.after(2000, self.check_companion_status)
        except Exception as e:
            self.add_to_log(f"Erreur lors du lancement du Companion: {e}", "error")
            self.companion_status.set("Erreur")
    
    def check_companion_status(self):
        """Vérifie le statut du Companion"""
        self.companion_status.set("Prêt")
        self.add_to_log("Companion est prêt", "info")
    
    def load_document(self):
        """Charge un document dans le système RAG"""
        file_path = filedialog.askopenfilename(
            title="Sélectionner un document",
            filetypes=[("Documents", "*.txt *.pdf *.docx *.py *.js *.html *.md"), ("Tous les fichiers", "*.*")]
        )
        if file_path:
            self.rag_status.set("Chargement...")
            self.add_to_log(f"Chargement du document: {file_path}", "info")
            
            # Simuler le chargement
            self.root.after(1000, lambda: self.complete_document_load(file_path))
    
    def complete_document_load(self, file_path):
        """Termine le chargement du document"""
        self.rag_status.set("Prêt")
        self.add_to_log(f"Document chargé: {os.path.basename(file_path)}", "info")
    
    def search_rag(self):
        """Effectue une recherche dans le système RAG"""
        self.add_to_log("Recherche RAG initiée", "info")
        # Simuler une recherche
        self.root.after(500, lambda: self.complete_rag_search())
    
    def complete_rag_search(self):
        """Termine la recherche RAG"""
        self.add_to_log("Recherche RAG terminée", "info")
    
    def index_rag(self):
        """Indexe le système RAG"""
        self.rag_status.set("Indexation...")
        self.add_to_log("Indexation RAG commencée", "info")
        
        # Simuler l'indexation
        self.root.after(2000, lambda: self.complete_rag_index())
    
    def complete_rag_index(self):
        """Termine l'indexation RAG"""
        self.rag_status.set("Prêt")
        self.add_to_log("Indexation RAG terminée", "info")
    
    def list_agents(self):
        """Liste les agents disponibles"""
        agents = ["fastflow-hx", "companion-search", "companion-tools", "system-info"]
        self.agent_status.set(f"Actif: {len(agents)} agents")
        self.add_to_log(f"Agents disponibles: {', '.join(agents)}", "info")
    
    def run_agent(self):
        """Exécute un agent"""
        self.agent_status.set("Exécution...")
        self.add_to_log("Exécution d'agent initiée", "info")
        
        # Simuler l'exécution
        self.root.after(1000, lambda: self.complete_agent_run())
    
    def complete_agent_run(self):
        """Termine l'exécution d'agent"""
        self.agent_status.set("Prêt")
        self.add_to_log("Exécution d'agent terminée", "info")
    
    def new_session(self):
        """Crée une nouvelle session"""
        self.add_to_log("Nouvelle session créée", "info")
        self.chat_display.config(state='normal')
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state='disabled')
        self.add_to_chat("Nouvelle session démarrée", "system")
    
    def reset_session(self):
        """Réinitialise la session"""
        if messagebox.askyesno("Confirmation", "Réinitialiser la session ?"):
            self.new_session()
    
    def export_session(self):
        """Exporte la session"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.chat_display.get("1.0", tk.END))
                self.add_to_log(f"Session exportée: {file_path}", "info")
            except Exception as e:
                self.add_to_log(f"Erreur lors de l'export: {e}", "error")
    
    def restart_npu(self):
        """Redémarre le NPU"""
        self.add_to_log("Redémarrage du NPU demandé", "info")
        # Simuler le redémarrage
        self.npu_var.set("NPU: Redémarrage...")
        self.root.after(2000, lambda: self.npu_var.set("NPU: 0%"))
    
    def clear_cache(self):
        """Nettoie le cache"""
        self.add_to_log("Cache nettoyé", "info")
    
    def generate_report(self):
        """Génère un rapport système"""
        report = f"""
Rapport Système HX365 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
================================================

Statut des services:
- FastFlowLM: {self.fastflowlm_status.get()}
- Companion: {self.companion_status.get()}
- RAG: {self.rag_status.get()}
- Agent: {self.agent_status.get()}

Statistiques système:
- {self.cpu_var.get()}
- {self.ram_var.get()}
- {self.npu_var.get()}

Sessions:
- Dernière activité: {datetime.now().strftime("%H:%M:%S")}
- Messages échangés: {self.get_message_count()}
        """
        
        # Afficher le rapport dans une nouvelle fenêtre
        report_window = tk.Toplevel(self.root)
        report_window.title("Rapport Système")
        report_window.geometry("600x400")
        report_window.configure(bg='#0a0a0f')
        
        report_text = scrolledtext.ScrolledText(report_window, bg='#151626', fg='#e2e8f0',
                                              insertbackground='#e2e8f0', font=('Consolas', 10))
        report_text.pack(fill='both', expand=True, padx=10, pady=10)
        report_text.insert('1.0', report)
        report_text.config(state='disabled')
    
    def get_message_count(self):
        """Compte les messages dans la zone de chat"""
        content = self.chat_display.get("1.0", tk.END)
        return len([line for line in content.split('\n') if line.strip()])
    
    def update_system_stats(self):
        """Met à jour les statistiques système"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_var.set(f"CPU: {cpu_percent}%")
            
            # RAM
            memory = psutil.virtual_memory()
            ram_used_gb = memory.used / (1024**3)
            self.ram_var.set(f"RAM: {ram_used_gb:.2f}GB ({memory.percent}%)")
            
            # NPU (simulation)
            # Dans une implémentation réelle, cela interrogerait les pilotes NPU
            npu_util = min(cpu_percent * 0.8, 100)  # Simulation basée sur CPU
            self.npu_var.set(f"NPU: {npu_util:.1f}%")
            
        except Exception as e:
            self.add_to_log(f"Erreur de surveillance système: {e}", "error")
        
        # Planifier la prochaine mise à jour
        self.root.after(2000, self.update_system_stats)
    
    def on_closing(self):
        """Fermeture de l'application"""
        # Arrêter les processus si nécessaire
        if self.fastflowlm_process:
            self.fastflowlm_process.terminate()
        
        self.root.destroy()

def main():
    """Fonction principale"""
    app = HX365TkinterGUI()
    
    # Lancer la boucle principale
    try:
        app.root.mainloop()
    except KeyboardInterrupt:
        print("\nArrêt de l'interface Tkinter...")
        app.on_closing()

if __name__ == "__main__":
    main()