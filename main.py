# -*- coding: utf-8 -*-

from random import random, randint, choice
from math import ceil, log
from bs4 import BeautifulSoup
import requests, csv

idEtudiant = 0 #pour identifier chaque étudiant, un identifiant unique, incrémenté pour chaque étudiant
nbPostulants = 700000

class Formation():
	def __init__(self, id, nom, filiere, nbPlaces):
		self.id, self.nom, self.filiere, self.nbPlaces = id, nom, filiere, nbPlaces
		self.candidats = []
		self.listeEtudiants = []

	def __str__(self): return self.nom+" "+self.filiere
	def __repr__(self): return self.nom+" "+self.filiere
	def __eq__(self, compare): return self is compare

	def ajoutCandidat(self, candidat):
		self.candidats.append(candidat)
	def triCandidats(self):
		anciensCandidats = self.candidats.copy()
		self.candidats = sorted(self.candidats)[:self.nbPlaces]

		for candidat in anciensCandidats:
			candidat.setDansFormation(self, candidat in self.candidats)
	def videCandidats(self):
		self.candidats = []
	def ouiDefinitif(self, etudiant):
		if etudiant not in self.listeEtudiants:
			self.listeEtudiants.append(etudiant) #l'étudiant est placé définitivement dans la formation
			self.nbPlaces -= 1 #comme un étudiant est placé définitivement, c'est une place de candidat en moins qui est disponible pour éviter le surbooking
			etudiant.dansFormation = self
			etudiant.voeuAccepte = self

	def getAcceptes(self): return self.candidats
	def estPlein(self): return len(self.candidats) >= self.nbPlaces or len(self.listeEtudiants) == self.nbPlaces
	def nbCases(self): return len(self.candidats)


class Etudiant():
	def __init__(self, prenom, nom, formations, comptePour=1):
		global idEtudiant

		self.nom, self.prenom, self.formations, self.comptePour = nom, prenom, formations, comptePour
		self.alea = randint(0,999999)
		self.dansFormation = False
		self.voeuAccepte = False
		self.voeuEnCours = 0
		self.id = idEtudiant
		idEtudiant += 1

		self.voeuRelatif = dict()
		for formation in formations: self.voeuRelatif[formation.filiere] = 0

	def __repr__(self):
		return self.prenom+" "+self.nom+" (id "+str(self.id).zfill(ceil(log(nbPostulants, 10)))+")"
	def __eq__(self, compare): return self.id == compare.id
	def __gt__(self, compare):
		#retourne True si le comparé est plus loin dans la liste d'attente que self
		filiere = self.formations[self.voeuEnCours].filiere

		if filiere not in compare.voeuRelatif:
			print(self.formations[self.voeuEnCours], filiere)
			print(compare.formations, compare.voeuEnCours, compare.voeuRelatif)

		return self.voeuRelatif[filiere] < compare.voeuRelatif[filiere]  or ((self.voeuRelatif[filiere] == compare.voeuRelatif[filiere] and self.voeuEnCours < compare.voeuEnCours) or (self.voeuEnCours == compare.voeuEnCours and self.alea < compare.alea))

	def postulePrefere(self):
		formation = self.formations[self.voeuEnCours]
		formation.ajoutCandidat(self)

		return formation

	def setDansFormation(self, formation, dansFormation):
		if dansFormation:
			self.dansFormation = formation
		else:
			self.voeuEnCours += 1
			self.voeuRelatif[formation.filiere] += 1

	def elimineFormations(self):
		self.formations = self.formations[:self.voeuEnCours+1] #on ne garde que les premiers voeux, jusqu'au dernier accepté

		if not self.voeuAccepte: #le candidat a répondu oui mais, il garde sa place dans la formation, mais espère en avoir une meilleure
			self.voeuAccepte = self.dansFormation
			self.dansFormation = False

			#on réinitialise les voeux, pour redemander les préférés
			self.voeuEnCours = 0
			for filiere in self.voeuRelatif: self.voeuRelatif[filiere] = 0

	def estDansFormation(self): return self.dansFormation
	def placeDuVoeu(self):
		try: return self.formations.index(self.voeuAccepte)
		except: return self.formations.index(self.dansFormation)
	def nbVoeux(self): return len(self.formations) - self.voeuEnCours

def prepPrenoms():
	listePrenoms = []

	try:
		for i in range(1, 3):
			source = requests.get("http://www.quelprenom.com/popularite.php?annee=2015&sexe="+str(i))
			code = source.text
			soup = BeautifulSoup(code, "html.parser")
			liste = soup.find("ul", class_="bn-list")
			for element in liste.find_all("li"):
				try:
					nbOccurences = 101 - int(element.span.string)
				except:
					pass
				prenom = str(element.a).split(">")[-2][1:-3]

				listePrenoms.append([prenom] * nbOccurences)
		listePrenoms = sum(listePrenoms, [])
	except:
		listePrenoms = ["".join([choice("azertyuiopqsdfghjklmwxcvbn") for _ in range(5)]) for _ in range(100)]

	return listePrenoms

def prepNoms():
	listeNoms = []

	try:
		source = requests.get("https://www.geneanet.org/genealogie/")
		code = source.text
		soup = BeautifulSoup(code, "html.parser")
		puces = soup.find("ul", id="noms")
		for puce in puces.find_all("li"):
			nom = puce.a.string
			occurences = str(puce).split("(")[1].split(")")[0].split()
			nbOccurences = round(int("".join(occurences)) / 10**5)

			listeNoms.append([nom] * nbOccurences)

		listeNoms = sum(listeNoms, [])
	except:
		listeNoms = ["".join([choice("azertyuiopqsdfghjklmwxcvbn") for _ in range(7)]) for _ in range(200)]

	return listeNoms

def prepFormations():
	formations = []

	with open("voeux-formations.csv", newline="") as fichier:
		reader = csv.DictReader(fichier, delimiter=";")

		colonnesOK = ["Code UAI de l'établissement d'accueil", "Libellé de l'établissement d'accueil", "Filières de formations", "Capacité de l'établissement par formation", "Effectif total des candidats"]
		for row in reader:
			id, nom, filiere, nbPlaces, nbCandidats = [row[x] for x in colonnesOK]
			if "inconnu" in (nbPlaces, nbCandidats) or nbCandidats == 0: continue
			nom += " ("+row["Départements"]+")"

			nbPlaces, nbCandidats = map(int, (nbPlaces, nbCandidats))
			formation = Formation(id, nom, filiere, nbPlaces)
			formations.append((formation, nbCandidats))

	return formations

def prepEtudiants(nbPostulants, listePrenoms, listeNoms, formations):
	formationsPond = []

	for formation, nbCandidats in formations:
		for _ in range(nbCandidats): formationsPond.append(formation)

	etudiants = []
	for i in range(nbPostulants):
		prenom, nom = choice(listePrenoms), choice(listeNoms)

		nbVoeux = randint(1, randint(5,24))
		voeuxFormations = []

		for _ in range(nbVoeux):
			possible = choice(formationsPond)
			while possible in voeuxFormations: possible = choice(formationsPond)

			voeuxFormations.append(possible)

		etudiants.append(Etudiant(nom, prenom, voeuxFormations))

	return etudiants

def attribution(formations, etudiants):
	nbPersDepart = len(etudiants)
	postulants = [x for x in etudiants if not x.estDansFormation() and x.nbVoeux() > 0]
	nbPostulantsTour = len(postulants)

	i = 0
	while len(postulants) > 0:
		for etudiant in postulants:
			etudiant.postulePrefere()

		for formation in formations:
			formation.triCandidats()

		postulants = [x for x in etudiants if not x.estDansFormation() and x.nbVoeux() > 0]
		nbPostulantsTourNew = len(postulants)

		i += 1
		nbPostulantsTour = nbPostulantsTourNew

	return i

def reacEtudiants(etudiants, formations, fin=False):
	etudiantsTourSuivant = []
	etudiantsOuiDefinitif = []

	voeuMoy, nbVoeuMoy = 0, 0
	for etudiant in etudiants:
		if not etudiant.estDansFormation(): #pas eu de place au tour qui vient de se finir, donc l'étudiant retente sa chance au tour suivant
			etudiantsTourSuivant.append(etudiant)
			continue

		#si on est là, c'est que l'étudiant a une place quelque part
		voeuMoy += etudiant.voeuEnCours
		nbVoeuMoy += 1

		if (etudiant.voeuEnCours == 0 and etudiant.estDansFormation()) or fin: #l'étudiant a son premier voeu ou c'est la fin de la procédure, donc oui définitif
			etudiantsOuiDefinitif.append(etudiant)
			formation = etudiant.dansFormation

			formation.ouiDefinitif(etudiant)
		else: #l'étudiant a une place, mais ce n'est pas son premier voeu. Il retente sa chance
			etudiantsTourSuivant.append(etudiant)

		#on élimine les voeux qui sont moins aimés par l'étudiant que le meilleur qu'il a eu
		etudiant.elimineFormations()

	for formation in formations: formation.videCandidats()

	return etudiantsTourSuivant, etudiantsOuiDefinitif, voeuMoy / nbVoeuMoy

def afficheReussiteParNoVoeu(etudiants):
	nbEtudiantsParNoVoeu = [0]*24

	nbRecales = 0
	for etudiant in etudiants:
		if etudiant.estDansFormation():
			nbEtudiantsParNoVoeu[etudiant.placeDuVoeu()] += 1
		else:
			nbRecales += 1

	for i in range(24):
		if nbEtudiantsParNoVoeu[i] > 0:
			print("Parmi les étudiants ayant une place,", nbEtudiantsParNoVoeu[i], "ont leur",str(i+1),"e voeu, soit", round(100*nbEtudiantsParNoVoeu[i]/sum(nbEtudiantsParNoVoeu),2),"%")

	print(nbRecales,"étudiants ont été recalés, soit", round(100*nbRecales/len(etudiants), 2), "%")

def enregistreListeCases(etudiants):
	with open("etudiantsOK.txt", "w") as fichier:
		printF = lambda x: fichier.write(x+"\n")

		for etudiant in [x for x in etudiants if x.estDansFormation()]:
			printF(str(etudiant)+" : "+str(etudiant.estDansFormation())+" (voeu n°"+str(etudiant.placeDuVoeu()+1)+")")

def enregistreListeRecales(etudiants):
	with open("etudiantsRestants.txt", "w") as fichier:
		printF = lambda x: fichier.write(x+"\n")

		for etudiant in [x for x in etudiants if not x.estDansFormation()]:
			printF(str(etudiant))

def enregistreListeFormationsOK(formations):
	with open("formationsOK.txt", "w") as fichier:
		printF = lambda x: fichier.write(x+"\n")

		for formation in [x for x in formations if x.estPlein()]:
			printF(str(formation)+" ("+str(formation.nbCases())+" places occupées)")

def enregistreFormationsRestantes(formations):
	with open("formationsRestantes.txt", "w") as fichier:
		printF = lambda x: fichier.write(x+"\n")

		for formation in [x for x in formations if not x.estPlein()]:
			printF(str(formation)+" : ("+str(len(formation.candidats))+" places restantes)")

def init(nbPostulants):
	listePrenoms = prepPrenoms()
	listeNoms = prepNoms()

	formations = prepFormations()
	print("Il y a",sum([x[0].nbPlaces for x in formations]),"places et",nbPostulants,"postulants...")

	print("Calcul des voeux des",nbPostulants,"étudiants en cours...")
	etudiants = prepEtudiants(nbPostulants, listePrenoms, listeNoms, formations)
	print("Calcul des voeux des", len(etudiants), "etudiants terminé !\n")

	formations = [x[0] for x in formations]

	return etudiants, formations

etudiants, formations = init(nbPostulants)
etudiantsPostulants = etudiants.copy()

while len(etudiantsPostulants) > 0:
	print("Calcul de l'attribution...")
	attribution(formations, etudiantsPostulants)
	print("Calcul de l'attribution terminé !")

	print("\nLes étudiants répondent...")
	etudiantsPostulants, etudiantsOkTour, voeuMoy = reacEtudiants(etudiants, formations)
	print("Les étudiants ont répondu\n")

	nbPlacesDef = len(etudiantsOkTour)
	nbOntPlace = nbPlacesDef + len([etudiant for etudiant in etudiantsPostulants if etudiant.voeuAccepte])

	print(nbPlacesDef,"étudiants ont confirmé définitivement leurs voeux")
	print(nbOntPlace,"étudiants ont été affectés quelque part sur les",len(etudiants),"(soit",round(100*nbOntPlace/len(etudiants),2),"%)")
	print("Numéro de voeu obtenu moyen :", round(1+voeuMoy, 10))

	print(len(etudiantsPostulants),"vont postuler au prochain tour,", len(etudiantsOkTour), "étudiants ont accepté définitivement leur voeu.")
	print()
	fin = "non" in input("Continuer ?").lower()
	print()

	if fin: break
etudiantsRecales, etudiantsOK, _ = reacEtudiants(etudiants, formations, fin=True)
etudiants = etudiantsRecales + etudiantsOK

afficheReussiteParNoVoeu(etudiants)
enregistreListeCases(etudiants)
enregistreListeRecales(etudiants)
enregistreListeFormationsOK(formations)
enregistreFormationsRestantes(formations)
