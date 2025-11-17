import io
from datetime import datetime

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


class EditeurPDF:
    """
    Classe pour ajouter plusieurs éléments de texte sur un PDF avant de générer le résultat.
    """

    def __init__(self, fichier_pdf_entree):
        """
        Initialise l'éditeur avec un fichier PDF.
        
        Paramètres:
        -----------
        fichier_pdf_entree : str
            Chemin du fichier PDF d'origine
        """
        self.fichier_pdf_entree = fichier_pdf_entree
        self.elements = []  # Liste pour stocker tous les éléments à ajouter

    def ajouter_texte(self,
                      texte,
                      x,
                      y,
                      page=0,
                      taille_police=12,
                      police="Helvetica",
                      couleur="#000000",
                      rotation=0,
                      opacite=1.0):
        """
        Ajoute un élément de texte à la liste (n'est pas appliqué immédiatement).
        
        Paramètres:
        -----------
        texte : str
            Le texte à ajouter
        x : float
            Position horizontale (en points, 0 = gauche)
        y : float
            Position verticale (en points, 0 = bas)
        page : int
            Numéro de la page (commence à 0)
        taille_police : int
            Taille de la police
        police : str
            Nom de la police (Helvetica, Times-Roman, Courier, etc.)
        couleur : str
            Couleur au format hexadécimal (#000000 pour noir)
        rotation : int
            Angle de rotation du texte (en degrés)
        opacite : float
            Opacité du texte (0.0 à 1.0)
        """
        self.elements.append({
            'type': 'texte',
            'texte': texte,
            'x': x,
            'y': y,
            'page': page,
            'taille_police': taille_police,
            'police': police,
            'couleur': couleur,
            'rotation': rotation,
            'opacite': opacite
        })
        print(f"✓ Texte ajouté: '{texte}' sur page {page} à ({x}, {y})")

    def ajouter_image(self,
                      chemin_image,
                      x,
                      y,
                      page=0,
                      largeur=None,
                      hauteur=None,
                      conserver_ratio=True,
                      rotation=0,
                      opacite=1.0):
        """
        Ajoute une image à la liste (n'est pas appliquée immédiatement).
        
        Paramètres:
        -----------
        chemin_image : str
            Chemin vers le fichier image (PNG, JPG, GIF, etc.)
        x : float
            Position horizontale (en points, 0 = gauche)
        y : float
            Position verticale (en points, 0 = bas)
        page : int
            Numéro de la page (commence à 0)
        largeur : float, optional
            Largeur de l'image en points (None = taille originale)
        hauteur : float, optional
            Hauteur de l'image en points (None = taille originale)
        conserver_ratio : bool
            Si True, conserve les proportions de l'image
        rotation : int
            Angle de rotation de l'image (en degrés)
        opacite : float
            Opacité de l'image (0.0 à 1.0)
        """
        self.elements.append({
            'type': 'image',
            'chemin_image': chemin_image,
            'x': x,
            'y': y,
            'page': page,
            'largeur': largeur,
            'hauteur': hauteur,
            'conserver_ratio': conserver_ratio,
            'rotation': rotation,
            'opacite': opacite
        })
        print(
            f"✓ Image ajoutée: '{chemin_image}' sur page {page} à ({x}, {y})")

    def generer(self, fichier_pdf_sortie):
        """
        Génère le PDF final avec tous les éléments ajoutés.
        
        Paramètres:
        -----------
        fichier_pdf_sortie : str
            Chemin du fichier PDF de sortie
        """
        # Lire le PDF existant
        lecteur_pdf = PdfReader(self.fichier_pdf_entree)
        sortie = PdfWriter()

        # Organiser les éléments par page
        elements_par_page = {}
        for elem in self.elements:
            page = elem['page']
            if page not in elements_par_page:
                elements_par_page[page] = []
            elements_par_page[page].append(elem)

        # Traiter chaque page
        for num_page in range(len(lecteur_pdf.pages)):
            page_existante = lecteur_pdf.pages[num_page]

            # S'il y a des éléments à ajouter sur cette page
            if num_page in elements_par_page:
                # Obtenir les dimensions de la page
                largeur = float(page_existante.mediabox.width)
                hauteur = float(page_existante.mediabox.height)

                # Créer un nouveau PDF avec tous les textes pour cette page
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=(largeur, hauteur))

                # Ajouter tous les éléments de texte
                for elem in elements_par_page[num_page]:
                    can.saveState()

                    if elem['type'] == 'texte':
                        # Configurer la police
                        can.setFont(elem['police'], elem['taille_police'])

                        # Configurer la couleur
                        can.setFillColor(HexColor(elem['couleur']))

                        # Configurer l'opacité
                        can.setFillAlpha(elem['opacite'])

                        # Gérer les sauts de ligne
                        lignes = elem['texte'].split('\n')

                        # Appliquer la rotation si nécessaire
                        if elem['rotation'] != 0:
                            can.translate(elem['x'], elem['y'])
                            can.rotate(elem['rotation'])
                            # Dessiner chaque ligne
                            for i, ligne in enumerate(lignes):
                                y_offset = -i * elem[
                                    'taille_police'] * 1.2  # Espacement entre lignes
                                can.drawString(0, y_offset, ligne)
                        else:
                            # Dessiner chaque ligne
                            for i, ligne in enumerate(lignes):
                                y_offset = elem['y'] - i * elem[
                                    'taille_police'] * 1.2  # Espacement entre lignes
                                can.drawString(elem['x'], y_offset, ligne)

                    elif elem['type'] == 'image':
                        from PIL import Image

                        # Ouvrir l'image pour obtenir ses dimensions
                        img = Image.open(elem['chemin_image'])
                        img_largeur, img_hauteur = img.size

                        # Déterminer les dimensions finales
                        if elem['largeur'] is None and elem['hauteur'] is None:
                            # Utiliser la taille originale
                            largeur_finale = img_largeur
                            hauteur_finale = img_hauteur
                        elif elem['largeur'] is not None and elem[
                                'hauteur'] is None:
                            # Largeur spécifiée, calculer la hauteur
                            largeur_finale = elem['largeur']
                            if elem['conserver_ratio']:
                                ratio = img_hauteur / img_largeur
                                hauteur_finale = largeur_finale * ratio
                            else:
                                hauteur_finale = img_hauteur
                        elif elem['largeur'] is None and elem[
                                'hauteur'] is not None:
                            # Hauteur spécifiée, calculer la largeur
                            hauteur_finale = elem['hauteur']
                            if elem['conserver_ratio']:
                                ratio = img_largeur / img_hauteur
                                largeur_finale = hauteur_finale * ratio
                            else:
                                largeur_finale = img_largeur
                        else:
                            # Les deux spécifiés
                            largeur_finale = elem['largeur']
                            hauteur_finale = elem['hauteur']

                        # Configurer l'opacité
                        can.setFillAlpha(elem['opacite'])
                        can.setStrokeAlpha(elem['opacite'])

                        # Appliquer la rotation si nécessaire
                        if elem['rotation'] != 0:
                            can.translate(elem['x'], elem['y'])
                            can.rotate(elem['rotation'])
                            can.drawImage(
                                elem['chemin_image'],
                                0,
                                0,
                                width=largeur_finale,
                                height=hauteur_finale,
                                preserveAspectRatio=elem['conserver_ratio'],
                                mask=
                                'auto'  # Active la transparence pour les PNG
                            )
                        else:
                            can.drawImage(
                                elem['chemin_image'],
                                elem['x'],
                                elem['y'],
                                width=largeur_finale,
                                height=hauteur_finale,
                                preserveAspectRatio=elem['conserver_ratio'],
                                mask=
                                'auto'  # Active la transparence pour les PNG
                            )

                    can.restoreState()

                can.save()
                packet.seek(0)

                # Fusionner avec la page existante
                nouveau_pdf = PdfReader(packet)
                page_existante.merge_page(nouveau_pdf.pages[0])

            sortie.add_page(page_existante)

        # Sauvegarder le résultat
        with open(fichier_pdf_sortie, "wb") as fichier_sortie:
            sortie.write(fichier_sortie)

        print(f"\n✓ PDF généré avec succès: {fichier_pdf_sortie}")
        print(f"  Total d'éléments ajoutés: {len(self.elements)}")

    def reinitialiser(self):
        """Supprime tous les éléments ajoutés."""
        self.elements = []
        print("✓ Tous les éléments ont été supprimés")


def signer_pdf_region(
    editeur_pdf,
    x,
    y,
    page=0,
    largeur=None,
    hauteur=None,
    conserver_ratio=True,
    chemin_logo_adobe="resources/adobe_logo.png",
):
    """
    Fonction utilitaire pour ajouter une signature à un PDF.
    
    Paramètres:
    -----------
    editeur_pdf : EditeurPDF
        Instance de l'éditeur PDF
    chemin_signature : str
        Chemin vers le fichier image de la signature
    x : float
        Position horizontale (en points, 0 = gauche)
    y : float
        Position verticale (en points, 0 = bas)
    page : int
        Numéro de la page (commence à 0)
    largeur : float, optional
        Largeur de l'image en points (None = taille originale)
    hauteur : float, optional
        Hauteur de l'image en points (None = taille originale)
    conserver_ratio : bool
        Si True, conserve les proportions de l'image
    opacite : float
        Opacité de l'image (0.0 à 1.0)
    """
    x_adobe = x + 135
    y_adobe = y - 35
    editeur_pdf.ajouter_image(chemin_image=chemin_logo_adobe,
                              x=x_adobe,
                              y=y_adobe,
                              page=page,
                              largeur=70,
                              hauteur=70,
                              conserver_ratio=conserver_ratio)

    editeur_pdf.ajouter_texte(
        texte="Lorem ipsum dolor sit amet, consectetur adipiscing elit. \n"
        "Pellentesque fermentum aliquam urna eu bibendum. \n"
        "Morbi sit amet blandit purus.",
        x=x,
        y=y,
        page=page,
        taille_police=6,
        police="Helvetica-Bold",
        couleur="#000000")

    x_signature = x_adobe + 35
    y_signature = y + 5
    editeur_pdf.ajouter_texte(
        texte="M. John Doe\n"
        "Certified Adobe\n"
        f"Signé le {datetime.now().strftime('%d/%m/%Y')}",
        x=x_signature,
        y=y_signature,
        page=page,
        taille_police=8,
        police="Helvetica-Bold",
        couleur="#000000")
    return editeur_pdf


# Exemples d'utilisation
if __name__ == "__main__":
    # Créer un éditeur PDF
    editeur = EditeurPDF("document.pdf")

    # # Ajouter plusieurs éléments
    signer_pdf_region(editeur,
                      x=50,
                      y=150,
                      page=0,
                      largeur=150,
                      hauteur=50,
                      conserver_ratio=True)

    # Générer le PDF final avec tous les éléments (textes + images)
    editeur.generer("document_complet_annote.pdf")
