####################################################################
#     casino BOT- PAR Maxime                                       #
#      Version 1.01                                                #
#                                                                  #
#  casino bot en python                                            #
####################################################################


import os
import irc
import socket
import re
import mariadb
import signal
import time
from datetime import datetime
import random
from colorama import Fore
from dotenv import load_dotenv

class Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Écriture du Pid
with open('bot.pid', 'w', encoding='utf-8') as f:
    f.write(str(os.getpid()))

# Configuration de la base de données
db_host = "localhost"
db_user = "nom-d'utulisateur-database"
db_password = "mot-de-pass-database"
db_name = "nom-de-la-database"

# Connexion à la base de données
try:
    conn = mariadb.connect(
        user=db_user,
        password=db_password,
        host=db_host,
        database=db_name
    )
    cursor = conn.cursor()
except mariadb.Error as e:
    print(f"Erreur de connexion à la base de données: {e}")
    exit(1)

# Fonction pour créer un compte utilisateur avec 1000 crédits à l'inscription
def creer_compte(nom_utilisateur):
    try:
        cursor.execute("INSERT INTO comptes (nom_utilisateur, solde_banque, solde_jeux, dernier_credit) VALUES (?, 1000, 0, ?)", (nom_utilisateur, datetime.now().date()))
        conn.commit()
        return True
    except mariadb.Error as e:
        print(f"Erreur lors de la création du compte: {e}")
        conn.rollback()
        return False

# Ajouter une fonction pour vérifier si un utilisateur est enregistré
def est_enregistre(nom_utilisateur):
    try:
        cursor.execute("SELECT * FROM comptes WHERE nom_utilisateur=?", (nom_utilisateur,))
        row = cursor.fetchone()
        return row is not None
    except mariadb.Error as e:
        print(f"Erreur lors de la vérification de l'enregistrement de l'utilisateur: {e}")
        return False

# Fonction pour récupérer le solde d'un utilisateur
def get_solde(nom_utilisateur):
    try:
        cursor.execute("SELECT solde_banque, solde_jeux FROM comptes WHERE nom_utilisateur=?", (nom_utilisateur,))
        row = cursor.fetchone()
        if row:
            return row
        else:
            return None
    except mariadb.Error as e:
        print(f"Erreur lors de la récupération du solde: {e}")
        return None

# Fonction pour récupérer le solde en banque d'un utilisateur
def get_solde_banque(nom_utilisateur):
    try:
        cursor.execute("SELECT solde_banque FROM comptes WHERE nom_utilisateur=?", (nom_utilisateur,))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return None
    except mariadb.Error as e:
        print(f"Erreur lors de la récupération du solde en banque: {e}")
        return None

def gestion_commande(nom_utilisateur, commande):
    mots = commande.split()
    if mots[0] == "!deposer":
        if len(mots) == 2:
            montant = int(mots[1])
            if montant > 0:
                solde_jeux = get_solde_jeux(nom_utilisateur)
                if solde_jeux is not None and solde_jeux >= montant:
                    nouveau_solde_jeux = solde_jeux - montant
                    solde_banque = get_solde_banque(nom_utilisateur)
                    if solde_banque is not None:
                        nouveau_solde_banque = solde_banque + montant
                        if mettre_a_jour_solde(nom_utilisateur, nouveau_solde_banque, nouveau_solde_jeux):
                            return f"{Fore.BLUE}Vous avez déposé {montant} crédits de jeux dans votre compte en banque. Nouveau solde en banque : {nouveau_solde_banque}, Nouveau solde en jeux : {nouveau_solde_jeux}"
                        else:
                            return f"{Fore.RED}Une erreur est survenue lors du dépôt."
                    else:
                        return f"{Fore.RED}Utilisateur non trouvé veuiller dabors vous enregistre avec la commande !register."
                else:
                    return f"{Fore.RED}Solde en jeux insuffisant."
            else:
                return f"{Fore.RED}Le montant doit être supérieur à zéro."
        else:
            return f"{Fore.RED}Commande invalide. Utilisation : !deposer [montant]"
    elif mots[0] == "!transfert":
        if len(mots) == 2:
            montant = int(mots[1])
            return transfert_credit(nom_utilisateur, montant)
        else:
            return f"{Fore.RED}Commande invalide. Utilisation : !transfert [montant]"
    elif mots[0] == "!convertir":
        if len(mots) == 2:
            montant = int(mots[1])
            if montant > 0:
                solde_jeux = get_solde_jeux(nom_utilisateur)
                if solde_jeux is not None and solde_jeux >= montant:
                    nouveau_solde_jeux = solde_jeux - montant
                    solde_banque = get_solde_banque(nom_utilisateur)
                    if solde_banque is not None:
                        nouveau_solde_banque = solde_banque + montant
                        if mettre_a_jour_solde(nom_utilisateur, nouveau_solde_banque, nouveau_solde_jeux):
                            return f"{Fore.BLUE}Vous avez converti {montant} crédits de jeux en {montant} crédits en banque. Nouveau solde en banque : {nouveau_solde_banque}, Nouveau solde en jeux : {nouveau_solde_jeux}"
                        else:
                            return f"{Fore.RED}Une erreur est survenue lors de la conversion."
                    else:
                        return f"{Fore.RED}Utilisateur non trouvé veuiller dabors vous enregistre avec la commande !register."
                else:
                    return f"{Fore.RED}Solde en jeux insuffisant."
            else:
                return f"{Fore.RED}Le montant doit être supérieur à zéro."
        else:
            return f"{Fore.RED}Commande invalide. Utilisation : !convertir [montant]"
    elif commande.startswith("!solde_banque"):
        solde_banque = get_solde_banque(nom_utilisateur)
        if solde_banque is not None:
            return f"{Fore.BLUE}Solde en banque : {solde_banque}"
        else:
            return f"{Fore.RED}Utilisateur non trouvé veuiller dabors vous enregistre avec la commande !register."
    elif commande.startswith("!solde_jeux"):
        solde_jeux = get_solde_jeux(nom_utilisateur)
        if solde_jeux is not None:
            return f"{Fore.BLUE}Solde en jeux : {solde_jeux}"
        else:
            return f"{Fore.RED}Utilisateur non trouvé veuiller dabors vous enregistre avec la commande !register."

    if not est_enregistre(nom_utilisateur):  # Vérifier si le joueur est enregistré
        return f"{Fore.RED}Vous devez d'abord vous enregistrer avec !register pour jouer.{Fore.END}"

def get_solde_jeux(nom_utilisateur):
    try:
        cursor.execute("SELECT solde_jeux FROM comptes WHERE nom_utilisateur=?", (nom_utilisateur,))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return None
    except mariadb.Error as e:
        print(f"{Fore.RED}Erreur lors de la récupération du solde de jeux: {e}{Fore.END}")
        return None

def mettre_a_jour_solde_banque(nom_utilisateur, nouveau_solde_banque):
    try:
        cursor.execute("UPDATE comptes SET solde_banque=? WHERE nom_utilisateur=?", (nouveau_solde_banque, nom_utilisateur))
        conn.commit()
        return True
    except mariadb.Error as e:
        print(f"{Fore.RED}Erreur lors de la mise à jour du solde en banque: {e}{Fore.END}")
        conn.rollback()
        return False

def mettre_a_jour_solde(nom_utilisateur, solde_banque, solde_jeux):
    try:
        cursor.execute("UPDATE comptes SET solde_banque=?, solde_jeux=? WHERE nom_utilisateur=?", (solde_banque, solde_jeux, nom_utilisateur))
        conn.commit()
        return True
    except mariadb.Error as e:
        print(f"{Fore.RED}Erreur lors de la mise à jour du solde: {e}{Fore.END}")
        conn.rollback()
        return False

def transfert_credit(nom_utilisateur, montant):
    solde_banque = get_solde_banque(nom_utilisateur)
    solde_jeux = get_solde_jeux(nom_utilisateur)

    if solde_banque is None:
        return f"{Fore.RED}Utilisateur non trouvé. Veuillez d'abord vous enregistrer avec la commande !register."

    if montant <= 0:
        return f"{Fore.RED}Le montant doit être supérieur à zéro."

    if solde_banque < montant:
        return f"{Fore.RED}Solde insuffisant dans votre compte en banque."

    nouveau_solde_banque = solde_banque - montant
    nouveau_solde_jeux = solde_jeux + montant

    if mettre_a_jour_solde(nom_utilisateur, nouveau_solde_banque, nouveau_solde_jeux):
        return f"{Fore.BLUE}Vous avez transféré {montant} crédits de votre compte en banque vers votre compte de jeux. Nouveau solde en banque : {nouveau_solde_banque}, Nouveau solde en jeux : {nouveau_solde_jeux}"
    else:
        return f"{Fore.RED}Une erreur est survenue lors du transfert de crédits."

def gestion_commande_casino(nom_utilisateur, commande):
    match = re.match(r"!casino (\d+)", commande)
    if match:
        montant = int(match.group(1))
        solde = get_solde(nom_utilisateur)
        solde_jeux = get_solde_jeux(nom_utilisateur)  # Récupérer le solde de jeux de l'utilisateur
        if solde_jeux:
            if solde:
                solde_banque, solde_jeux = solde
                if solde_banque >= montant:
                    if gagner_ou_perdre():
                        solde_banque -= montant
                        solde_jeux += montant * 2  
                        message = f"{Fore.BLUE}Vous avez gagné {montant} ! Votre nouveau solde en jeux est de {solde_jeux}.{Fore.RESET}"
                    else:
                        solde_banque -= montant
                        solde_jeux -= montant  
                        message = f"{Fore.RED}Vous avez perdu {montant} ! Votre solde en banque est de {solde_banque}. Votre solde en jeux est de {solde_jeux}.{Color.END}"
                    if mettre_a_jour_solde(nom_utilisateur, solde_banque, solde_jeux):
                        return message
                    else:
                        return f"{Color.PURPLE}Solde insuffisant dans votre banque.{Color.END}"
                else:
                    return f"{Color.PURPLE}Solde insuffisant dans votre banque.{Color.END}"

        else:
            return f"{Fore.RED}Vous n'avez pas suffisamment de crédits de jeux pour jouer veuillez faire un transfert [!transfert montant].{Color.END}"
    else:
        return f"{Fore.RED}Commande invalide. Utilisation : !casino [montant]{Fore.END}"

def gestion_commande_roulette(nom_utilisateur, commande):
    mots = commande.split()
    if mots[0] == "!roulette":
        if len(mots) == 2:
            montant = int(mots[1])
            solde = get_solde(nom_utilisateur)
            if solde:
                solde_banque, solde_jeux = solde
                if solde_banque >= montant:
                    resultat_jeu = jeu_roulette()
                    numero_gagnant, couleur, parite = resultat_jeu
                    if numero_gagnant == 0:
                        solde_jeux -= montant  
                        message = f"La bille est tombée sur le 0. Vous avez perdu {montant} crédits ! Votre solde en banque est de {solde_banque}. Votre solde en jeux est de {solde_jeux}."
                    else:
                        if gagner_ou_perdre():
                            solde_banque -= montant
                            solde_jeux += montant * 2  
                            message = f"La bille est tombée sur le {numero_gagnant} ({couleur}, {parite}). Vous avez gagné {montant} crédits ! Votre solde en banque est de {solde_banque}. Votre solde en jeux est de {solde_jeux}."
                        else:
                            solde_banque -= montant
                            solde_jeux -= montant  
                            message = f"La bille est tombée sur le {numero_gagnant} ({couleur}, {parite}). Vous avez perdu {montant} crédits ! Votre solde en banque est de {solde_banque}. Votre solde en jeux est de {solde_jeux}."
                    if mettre_a_jour_solde(nom_utilisateur, solde_banque, solde_jeux):
                        return message
                    else:
                        return f"{Fore.RED}Une erreur est survenue lors de la mise à jour du solde.{Fore.END}"
                else:
                    return "Solde insuffisant dans votre banque."
            else:
                return "Utilisateur non trouvé veuiller dabors vous enregistre avec la commande !register."
        else:
            return "Commande invalide. Utilisation : !roulette [montant]"
    else:
        return "Commande invalide."

# Définition de la variable globale symboles
symboles = {
    "🍒": 10,
    "🍊": 20,
    "🍋": 30,
    "🍉": 40,
    "🍇": 50,
    "🔔": 75,
    "💎": 100,
    "🎰": 200
}

# Initialisation de la variable globale jackpot
jackpot = 1

def jeu_slots(nom_utilisateur, montant_mise):
    solde_banque = get_solde_banque(nom_utilisateur)
    if solde_banque is not None and solde_banque >= montant_mise:
        solde_banque -= montant_mise
        symboles_tires = [random.choice(list(symboles.keys())) for _ in range(3)]  
        resultat = [symboles[symbole] for symbole in symboles_tires]  
        symboles_alignes = len(set(symboles_tires))

        if jackpot == 1 and symboles_alignes == 1:
            jackpot_amount = random.randint(1000, 10000)
            solde_jeux = get_solde_jeux(nom_utilisateur)
            solde_jeux += jackpot_amount
            mettre_a_jour_solde(nom_utilisateur, solde_banque, solde_jeux)
            return f"Jackpot !! Vous avez gagné {jackpot_amount} crédits de jeux ! Résultat: {' - '.join(symboles_tires)}."

        if symboles_alignes == 2:
            gain = montant_mise * 2  
            solde_jeux = get_solde_jeux(nom_utilisateur)
            solde_jeux += gain  
            mettre_a_jour_solde(nom_utilisateur, solde_banque, solde_jeux)
            return f"Bravo ! Vous avez gagné {gain} crédits de jeux ! Résultat: {' - '.join(symboles_tires)}."
        else:
            mettre_a_jour_solde_banque(nom_utilisateur, solde_banque)
            return f"Dommage ! Vous n'avez rien gagné cette fois-ci. Résultat: {' - '.join(symboles_tires)}."
    else:
        return "Solde insuffisant dans votre banque pour effectuer cette mise."

articles = {
    "Livre": 50,
    "Montre": 100,
    "Console de jeu": 200,
    "Vélo": 300,
    "Smartphone": 500
}

def jeu_juste_prix(nom_utilisateur, montant_mise):
    prix_a_deviner = random.randint(1, 100)  
    if montant_mise <= 0:
        return "Le montant misé doit être supérieur à zéro."
    solde_banque = get_solde_banque(nom_utilisateur)
    if solde_banque is not None and solde_banque >= montant_mise:
        solde_banque -= montant_mise
        numero_propose = random.randint(1, 100)  
        if numero_propose == prix_a_deviner:
            solde_jeux = get_solde_jeux(nom_utilisateur)
            solde_jeux += montant_mise * 2  
            article_gagne = attribuer_article(montant_mise)
            mettre_a_jour_solde(nom_utilisateur, solde_banque, solde_jeux)
            return f"Bravo ! Vous avez deviné le juste prix ({prix_a_deviner}) ! Vous avez gagné {montant_mise * 2} crédits de jeux et un(e) {article_gagne}."
        else:
            solde_jeux = get_solde_jeux(nom_utilisateur)
            solde_jeux -= montant_mise  
            mettre_a_jour_solde(nom_utilisateur, solde_banque, solde_jeux)
            return f"Dommage ! Le juste prix était {prix_a_deviner}. Vous avez perdu votre mise."
    else:
        return "Solde insuffisant dans votre banque pour effectuer cette mise."

def attribuer_article(montant_mise):
    for article, valeur in articles.items():
        if montant_mise * 2 >= valeur:  
            return article
    return "Aucun article"

def gagner_ou_perdre():
    return random.choice([True, False])

def jeu_roulette():
    numero_gagnant = random.randint(0, 36)

    if numero_gagnant % 2 == 0:
        parite = "pair"
    else:
        parite = "impair"

    if numero_gagnant == 0:
        couleur = "vert"
    elif (numero_gagnant >= 1 and numero_gagnant <= 10) or (numero_gagnant >= 19 and numero_gagnant <= 28):
        if numero_gagnant % 2 == 0:
            couleur = "noir"
        else:
            couleur = "rouge"
    else:
        if numero_gagnant % 2 == 0:
            couleur = "rouge"
        else:
            couleur = "noir"

    return numero_gagnant, couleur, parite

# Définir une liste d'administrateurs autorisés
administrateurs = ["Maxime", "KoS_"]  # Remplacez ceci par les noms des administrateurs réels

# Ajouter une fonction pour envoyer de l'aide
def envoyer_aide(nom_utilisateur):
    if nom_utilisateur in administrateurs:
        irc.send(f"PRIVMSG {nom_utilisateur} :\x0304Commandes disponibles (administrateur) :\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !register [nom_utilisateur] : Créer un compte.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !solde [nom_utilisateur] : Voir le solde du compte.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !convertir [montant] converti vos credit de jeux et les met en banque.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !transfert [montant] : transfert des crédits de votre compte en banque vers votre compte de jeux.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !roulette [nombre] : jouer au jeux de la roulette.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !casino [jeu] [montant] : joue au jeu du casino (ex: !casino 50).\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !slots [montant] : joue au machine a sous.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !quit : Déconnecter le bot.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !join [#channel] : fait joindre le bot sur un channel.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !part [#channel] : fait Partire le bot d'un channel.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !supprime [nom_utilisateur] : Supprimer un compte.\n".encode())
    else:
        irc.send(f"PRIVMSG {nom_utilisateur} :\x0304Commandes disponibles :\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !register [nom_utilisateur] : Créer un compte.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !solde [nom_utilisateur] : Voir le solde du compte.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !convertir [montant] converti vos credit de jeux et les met en banque.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !casino [jeu] [montant] : joue au jeu du casino (ex: !casino 50).\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !roulette [nombre] : jouer au jeux de la roulette.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !slots [montant] : joue au machine a sous.\n".encode())

# Ajouter une commande pour supprimer un compte
def supprimer_compte(administrateur):
    try:
        cursor.execute("DELETE FROM comptes WHERE nom_utilisateur=?", (administrateur,))
        conn.commit()
        return True
    except mariadb.Error as e:
        print(f"Erreur lors de la suppression du compte: {e}")
        conn.rollback()
        return False

# Configuration IRC
server = "irc.extra-cool.fr"
port = 6667
channel = "#casino"
bot_name = "CasinoBot"

# Création de la socket pour la connexion IRC
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc.connect((server, port))
irc.send(f"USER {bot_name} {bot_name} {bot_name} :IRC Bot\n".encode())
irc.send(f"NICK {bot_name}\n".encode())
irc.send(f"JOIN {channel}\n".encode())
irc.send("JOIN #logs\n".encode())  # S'assurer de rejoindre le salon #logs


def log_commande(message):
    irc.send(f"PRIVMSG #logs :{message}\n".encode())


# Boucle principale pour traiter les messages
while True:
    message = irc.recv(2048).decode("UTF-8")
    print(message)  # Afficher le message pour le débogage

    # Répondre aux PINGs du serveur pour garder la connexion active
    if "PING" in message:
        # Extraction du 'cookie' (token PING) du message
        cookie = message.split()[1]
        irc.send(f"PONG {cookie}\n".encode())
        log_commande(f"PING/PONG maintenu avec {cookie}")

    # Gérer le message d'erreur spécifique pour le salon #logs
    if "404" in message and "#logs" in message:
        print("Erreur : Le bot ne peut pas poster dans #logs en raison de restrictions.")
        irc.send(f"JOIN #logs\n".encode())  # Essayer de rejoindre à nouveau si non présent
        # Envisager d'envoyer un message à un administrateur ici
        continue

    elif "PRIVMSG" in message:
        sender_match = re.match(r"^:(.*?)!", message)
        channel_match = re.search(r"PRIVMSG (#\S+)", message)
        msg_match = re.search(r"PRIVMSG #\S+ :(.*)", message)

        if sender_match and channel_match and msg_match:
            sender = sender_match.group(1)
            channel = channel_match.group(1)
            msg = msg_match.group(1).strip()

            # Log toutes les commandes reçues
            log_commande(f"Commande reçue de {sender} sur {channel}: {msg}")

            if msg.startswith("!register"):
                mots = msg.split()
                if len(mots) >= 2:
                    nom_utilisateur = mots[1]
                    if creer_compte(nom_utilisateur):
                        irc.send(f"PRIVMSG {channel} :Compte {nom_utilisateur} créé avec succès.\n".encode())
                        log_commande(f"Compte {nom_utilisateur} créé avec succès par {sender}")
                    else:
                        irc.send(f"PRIVMSG {channel} :Erreur lors de la création du compte.\n".encode())
                        log_commande(f"Erreur lors de la création du compte pour {nom_utilisateur} par {sender}")
                else:
                    irc.send(f"PRIVMSG {channel} :Commande invalide. Utilisation : !register [nom_utilisateur]\n".encode())
                    log_commande(f"Tentative de création de compte avec commande invalide par {sender}")

            elif msg.startswith("!solde"):
                mots = msg.split()
                if len(mots) >= 2:
                    nom_utilisateur = mots[1]
                    solde = get_solde(nom_utilisateur)
                    if solde:
                        solde_banque, solde_jeux = solde
                        irc.send(f"PRIVMSG {channel} :Solde en banque : {solde_banque}, Solde en jeux : {solde_jeux}\n".encode())
                        log_commande(f"Solde vérifié pour {nom_utilisateur} par {sender}")
                    else:
                        irc.send(f"PRIVMSG {channel} :Utilisateur non trouvé veuiller d'abord vous enregistrer avec la commande !register.\n".encode())
                        log_commande(f"Utilisateur non trouvé pour vérification de solde par {sender}")
                else:
                    irc.send(f"PRIVMSG {channel} :Commande invalide. Utilisation : !solde [nom_utilisateur]\n".encode())
                    log_commande(f"Commande invalide pour solde effectuée par {sender}")

            elif msg.startswith("!casino"):
                mots = msg.split()
                if len(mots) >= 2:
                    nom_utilisateur = sender
                    commande = msg
                    response = gestion_commande_casino(nom_utilisateur, commande)
                    irc.send(f"PRIVMSG {channel} :{response}\n".encode())
                else:
                    irc.send(f"PRIVMSG {channel} :Commande invalide. Utilisation : !casino [montant]\n".encode())
            elif msg.startswith("!roulette"):
                mots = msg.split()
                if len(mots) >= 2:
                    nom_utilisateur = sender
                    commande = msg
                    response = gestion_commande_roulette(nom_utilisateur, commande)
                    irc.send(f"PRIVMSG {channel} :{response}\n".encode())
                else:
                    irc.send(f"PRIVMSG {channel} :Commande invalide. Utilisation : !roulette [montant]\n".encode())

            # Gestion des commandes administratives
            elif msg.startswith("!supprimer"):
                if sender in administrateurs:
                    mots = msg.split()
                    if len(mots) >= 2:
                        nom_utilisateur = mots[1]
                        if supprimer_compte(nom_utilisateur):
                            irc.send(f"PRIVMSG {channel} :Compte {nom_utilisateur} supprimé avec succès.\n".encode())
                        else:
                            irc.send(f"PRIVMSG {channel} :Erreur lors de la suppression du compte.\n".encode())
                    else:
                        irc.send(f"PRIVMSG {channel} :Commande invalide. Utilisation : !supprimer [nom_utilisateur]\n".encode())
                else:
                    irc.send(f"PRIVMSG {channel} :Vous n'êtes pas autorisé à exécuter cette commande.\n".encode())

            elif msg.startswith("!transfert"):
                mots = msg.split()
                if len(mots) == 2:
                    montant = int(mots[1])
                    response = gestion_commande(sender, msg)
                    irc.send(f"PRIVMSG {channel} :{response}\n".encode())
                    log_commande(f"Transfert de {montant} crédits effectué par {sender}")
                else:
                    irc.send(f"PRIVMSG {channel} :Commande invalide. Utilisation : !transfert [montant]\n".encode())
                    log_commande(f"Commande invalide !transfert par {sender}")

            elif msg.startswith("!casino"):
                mots = msg.split()
                if len(mots) >= 2:
                    nom_utilisateur = sender
                    commande = msg
                    response = gestion_commande_casino(nom_utilisateur, commande)
                    irc.send(f"PRIVMSG {channel} :{response}\n".encode())
                    log_commande(f"Casino commandé par {sender} avec la mise {mots[1]}")
                else:
                    irc.send(f"PRIVMSG {channel} :Commande invalide. Utilisation : !casino [montant]\n".encode())
                    log_commande(f"Commande invalide !casino par {sender}")

            elif msg.startswith("!roulette"):
                mots = msg.split()
                if len(mots) >= 2:
                    nom_utilisateur = sender
                    commande = msg
                    response = gestion_commande_roulette(nom_utilisateur, commande)
                    irc.send(f"PRIVMSG {channel} :{response}\n".encode())
                    log_commande(f"Roulette jouée par {sender} avec mise de {mots[1]}")
                else:
                    irc.send(f"PRIVMSG {channel} :Commande invalide. Utilisation : !roulette [montant]\n".encode())
                    log_commande(f"Commande invalide !roulette par {sender}")

            elif msg.startswith("!join"):
                if sender in administrateurs:
                    mots = msg.split()
                    if len(mots) == 2:
                        channel_to_join = mots[1]
                        irc.send(f"JOIN {channel_to_join}\n".encode())
                        irc.send(f"PRIVMSG {channel} :je rejoint {channel_to_join} le salon.\n".encode())
                        log_commande(f"{sender} a fait rejoindre le bot au salon {channel_to_join}")
                    else:
                        irc.send(f"PRIVMSG {sender} :Commande invalide. Utilisation : !join [nom_du_salon]\n".encode())
                        log_commande(f"Commande invalide !join par {sender}")
                else:
                    irc.send(f"PRIVMSG {sender} :Vous n'êtes pas autorisé à utiliser cette commande.\n".encode())
                    log_commande(f"Tentative d'accès non autorisée à la commande !join par {sender}")

            elif msg.startswith("!part"):
                if sender in administrateurs:
                    mots = msg.split()
                    if len(mots) == 2:
                        channel_to_leave = mots[1]
                        irc.send(f"PART {channel_to_leave}\n".encode())
                        irc.send(f"PRIVMSG {channel} :ok je quitte le salon {channel_to_leave} ah bientôt.\n".encode())
                        log_commande(f"{sender} a fait quitter le bot du salon {channel_to_leave}")
                    else:
                        irc.send(f"PRIVMSG {sender} :Commande invalide. Utilisation : !part [nom_du_salon]\n".encode())
                        log_commande(f"Commande invalide !part par {sender}")
                else:
                    irc.send(f"PRIVMSG {sender} :Vous n'êtes pas autorisé à utiliser cette commande.\n".encode())
                    log_commande(f"Tentative d'accès non autorisée à la commande !part par {sender}")

            elif msg.startswith("!quit"):
                if sender in administrateurs:
                    irc.send("QUIT Maintenance Technique bot casino beta-0.01 by Max\n".encode())
                    pid = open("bot.pid", "r").read().strip()
                    os.kill(int(pid), signal.SIGTERM)
                    log_commande(f"Bot quitte sur commande par {sender}")
                else:
                    irc.send(f"PRIVMSG {sender} :Vous n'êtes pas autorisé à utiliser cette commande.\n".encode())
                    log_commande(f"Tentative d'accès non autorisée à la commande !quit par {sender}")

# Fermeture de la connexion
irc.close()
