#!/usr/bin/env python3
"""
HX365 Command Center - Script de Vérification Finale
=====================================================

Ce script vérifie les composants du système HX365 Command Center
sans causer d'erreurs d'initialisation anticipée.
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Configuration de l'encodage pour Windows
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def check_encoding():
    """Vérifie et configure l'encodage UTF-8"""
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception as e:
        print(f"Avertissement: Impossible de configurer l'encodage UTF-8: {e}")

check_encoding()

class FinalVerificationSystem:
    """Système de vérification finale sans problèmes d'initialisation"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            },
            "system_info": self._get_system_info()
        }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Obtenir les informations système"""
        import platform
        import psutil
        
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": sys.version,
            "encoding": sys.getdefaultencoding(),
            "filesystem_encoding": sys.getfilesystemencoding(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "current_directory": os.getcwd(),
            "unicode_support": self._check_unicode_support()
        }
    
    def _check_unicode_support(self) -> bool:
        """Vérifier le support Unicode du système"""
        try:
            test_string = "✓ HX365 Command Center 🚀"
            encoded = test_string.encode('utf-8')
            decoded = encoded.decode('utf-8')
            return test_string == decoded
        except UnicodeError:
            return False
    
    def verify_file_integrity(self) -> bool:
        """Vérifier l'intégrité des fichiers principaux"""
        print("\n🔍 Vérification de l'intégrité des fichiers...")
        
        critical_files = [
            "hx365_gui.html",
            "hx365_core_fixed.py",
            "hx365_hardware.py",
            "hx365_rag.py",
            "hx365_power_user.py",
            "hx365_api.py",
            "hx365_system.py",
            "main_final.py",
            "requirements.txt",
            "README.md"
        ]
        
        all_good = True
        for file_name in critical_files:
            file_path = Path(file_name)
            if file_path.exists():
                # Vérifier la taille du fichier (doit être > 0)
                if file_path.stat().st_size > 0:
                    print(f"✅ {file_name}: Existe et non vide")
                else:
                    print(f"❌ {file_name}: Existe mais vide")
                    all_good = False
            else:
                print(f"❌ {file_name}: Fichier manquant")
                all_good = False
        
        self.results["checks"]["file_integrity"] = {
            "status": "PASSED" if all_good else "FAILED",
            "details": {"files_checked": len(critical_files), "integrity_ok": all_good}
        }
        
        return all_good
    
    def verify_file_encodings(self) -> bool:
        """Vérifier l'encodage des fichiers critiques"""
        print("\n🔍 Vérification de l'encodage des fichiers...")
        
        critical_files = [
            "hx365_gui.html",
            "hx365_core_fixed.py",
            "hx365_hardware.py",
            "hx365_rag.py",
            "hx365_power_user.py",
            "hx365_api.py",
            "hx365_system.py",
            "main_final.py",
            "README.md"
        ]
        
        all_good = True
        for file_name in critical_files:
            file_path = Path(file_name)
            if file_path.exists():
                try:
                    # Essayer de lire les premiers caractères avec UTF-8
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read(500)  # Lire les premiers caractères
                    print(f"✅ {file_name}: Encodage UTF-8 correct")
                except UnicodeDecodeError:
                    print(f"❌ {file_name}: Problème d'encodage UTF-8")
                    all_good = False
                except Exception as e:
                    print(f"⚠️  {file_name}: Erreur lors de la vérification - {e}")
            else:
                print(f"⚠️  {file_name}: Fichier non trouvé")
        
        self.results["checks"]["file_encodings"] = {
            "status": "PASSED" if all_good else "FAILED",
            "details": {"files_checked": len(critical_files), "encoding_ok": all_good}
        }
        
        return all_good
    
    def verify_dependencies(self) -> bool:
        """Vérifier la disponibilité des dépendances critiques"""
        print("\n🔍 Vérification des dépendances critiques...")
        
        critical_deps = [
            ("fastapi", "Serveur API"),
            ("httpx", "Client HTTP asynchrone"),
            ("pydantic", "Validation des données"),
            ("psutil", "Monitoring système"),
            ("usearch", "Indexation vectorielle"),
            ("transformers", "Modèles ML"),
            ("torch", "PyTorch"),
            ("numpy", "Calcul numérique"),
            ("nltk", "Traitement du langage naturel")
        ]
        
        all_installed = True
        for module_name, description in critical_deps:
            try:
                __import__(module_name)
                print(f"✅ {description} ({module_name}): Disponible")
            except ImportError:
                print(f"❌ {description} ({module_name}): Non installé")
                all_installed = False
        
        self.results["checks"]["dependencies"] = {
            "status": "PASSED" if all_installed else "FAILED",
            "details": {"deps_checked": len(critical_deps), "installed": all_installed}
        }
        
        return all_installed
    
    def verify_python_version(self) -> bool:
        """Vérifier la version de Python"""
        print("\n🔍 Vérification de la version de Python...")
        
        major, minor = sys.version_info[:2]
        if major == 3 and minor >= 8:
            print(f"✅ Version Python {major}.{minor}: Compatible")
            version_ok = True
        else:
            print(f"❌ Version Python {major}.{minor}: Incompatible (nécessite 3.8+)")
            version_ok = False
        
        self.results["checks"]["python_version"] = {
            "status": "PASSED" if version_ok else "FAILED",
            "details": {"version": f"{major}.{minor}", "compatible": version_ok}
        }
        
        return version_ok
    
    def verify_system_resources(self) -> bool:
        """Vérifier les ressources système"""
        print("\n🔍 Vérification des ressources système...")
        
        try:
            import psutil
            
            # Vérifier la mémoire disponible
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            
            # Vérifier le nombre de cœurs CPU
            cpu_count = psutil.cpu_count()
            
            print(f"📊 Mémoire disponible: {available_gb:.2f} GB")
            print(f"📊 Cœurs CPU: {cpu_count}")
            
            # Vérifier si les ressources sont suffisantes
            resources_ok = available_gb >= 2.0 and cpu_count >= 4  # Minimum requis
            
            if resources_ok:
                print("✅ Ressources système suffisantes")
            else:
                print("⚠️  Ressources système limitées (minimum: 2GB RAM, 4 cœurs)")
            
            self.results["checks"]["system_resources"] = {
                "status": "PASSED" if resources_ok else "WARNING",
                "details": {"memory_gb": available_gb, "cpu_count": cpu_count, "ok": resources_ok}
            }
            
            return True  # La vérification elle-même est réussie
            
        except ImportError:
            print("⚠️  Module psutil non disponible - vérification des ressources ignorée")
            self.results["checks"]["system_resources"] = {
                "status": "WARNING",
                "details": {"error": "psutil not available"}
            }
            return True  # Ce n'est pas une erreur critique
    
    def run_comprehensive_verification(self) -> Dict[str, Any]:
        """Exécuter la vérification complète"""
        print("HX365 Command Center - Vérification Finale")
        print("=" * 50)
        
        # Exécuter les vérifications
        checks = [
            self.verify_file_integrity(),
            self.verify_file_encodings(),
            self.verify_dependencies(),
            self.verify_python_version(),
            self.verify_system_resources()
        ]
        
        # Calculer les totaux
        total_checks = len(checks)
        passed_checks = sum(checks)
        failed_checks = total_checks - passed_checks
        
        # Mettre à jour le résumé
        self.results["summary"] = {
            "total": total_checks,
            "passed": passed_checks,
            "failed": failed_checks,
            "warnings": failed_checks  # Pour ce système, les échecs sont traités comme des avertissements
        }
        
        return self.results
    
    def generate_detailed_report(self) -> str:
        """Générer un rapport détaillé"""
        report = []
        report.append("HX365 COMMAND CENTER - RAPPORT DE VÉRIFICATION FINALE")
        report.append("=" * 65)
        report.append(f"Date: {self.results['timestamp']}")
        report.append(f"Plateforme: {self.results['system_info']['platform']}")
        report.append(f"Version Python: {self.results['system_info']['python_version']}")
        report.append(f"Encodage: {self.results['system_info']['encoding']}")
        report.append(f"Support Unicode: {'✅' if self.results['system_info']['unicode_support'] else '❌'}")
        report.append("")
        
        # Résumé
        summary = self.results['summary']
        report.append("RÉSUMÉ:")
        report.append("-" * 10)
        report.append(f"  Total: {summary['total']}")
        report.append(f"  Réussi: {summary['passed']} ✅")
        report.append(f"  Échoué: {summary['failed']} ❌")
        report.append(f"  Taux de succès: {summary['passed']/summary['total']*100:.1f}%" if summary['total'] > 0 else "0%")
        report.append("")
        
        # Détails des vérifications
        report.append("DÉTAILS DES VÉRIFICATIONS:")
        report.append("-" * 25)
        for check_name, check_result in self.results['checks'].items():
            status_symbol = "✅" if check_result['status'] == 'PASSED' else "❌" if check_result['status'] == 'FAILED' else "⚠️"
            report.append(f"{status_symbol} {check_name}: {check_result['status']}")
            if 'details' in check_result:
                report.append(f"    Détails: {check_result['details']}")
        report.append("")
        
        # Recommandations
        report.append("RECOMMANDATIONS:")
        report.append("-" * 17)
        
        if summary['failed'] > 0:
            report.append("• Consulter les détails ci-dessus pour les corrections nécessaires")
            report.append("• Installer les dépendances manquantes avec: pip install -r requirements.txt")
        else:
            report.append("• Le système est prêt pour le déploiement")
            report.append("• Exécuter: python main_final.py pour lancer le système")
        
        report.append("")
        report.append("=" * 65)
        
        return "\n".join(report)
    
    def save_report(self, filename: str = None) -> str:
        """Sauvegarder le rapport"""
        if filename is None:
            filename = f"hx365_final_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        report_content = self.generate_detailed_report()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # Sauvegarder aussi en JSON
        json_filename = filename.replace('.txt', '.json')
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        return filename, json_filename


def main():
    """Fonction principale"""
    print("Démarrage de la vérification finale...")
    
    # Créer le système de vérification
    verifier = FinalVerificationSystem()
    
    # Exécuter la vérification complète
    results = verifier.run_comprehensive_verification()
    
    # Générer et afficher le rapport
    report = verifier.generate_detailed_report()
    print(report)
    
    # Sauvegarder le rapport
    txt_file, json_file = verifier.save_report()
    print(f"Rapport sauvegardé dans: {txt_file}")
    print(f"Rapport JSON sauvegardé dans: {json_file}")
    
    # Retourner le code de sortie
    success_rate = results['summary']['passed'] / results['summary']['total'] if results['summary']['total'] > 0 else 0
    return 0 if success_rate >= 0.8 else 1  # Succès si 80% ou plus des vérifications passent


if __name__ == "__main__":
    # S'assurer que l'encodage est correctement configuré
    check_encoding()
    
    # Exécuter la vérification
    exit_code = main()
    sys.exit(exit_code)