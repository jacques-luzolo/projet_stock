CREATE DATABASE IF NOT EXISTS gestion_stock
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE gestion_stock;

CREATE TABLE IF NOT EXISTS roles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(30) NOT NULL UNIQUE,
  description VARCHAR(150)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS utilisateurs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(80) NOT NULL,
  prenom VARCHAR(80),
  email VARCHAR(120) NOT NULL UNIQUE,
  login VARCHAR(50) NOT NULL UNIQUE,
  mot_de_passe_hash VARCHAR(255) NOT NULL,
  role_id INT NOT NULL,
  actif BOOLEAN DEFAULT TRUE,
  derniere_connexion DATETIME NULL,
  cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_user_role FOREIGN KEY (role_id) REFERENCES roles(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS categories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(80) NOT NULL UNIQUE,
  description TEXT,
  parent_id INT NULL,
  CONSTRAINT fk_cat_parent FOREIGN KEY (parent_id) REFERENCES categories(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fournisseurs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  raison_sociale VARCHAR(150) NOT NULL,
  contact VARCHAR(100),
  telephone VARCHAR(30),
  email VARCHAR(120),
  adresse TEXT,
  ville VARCHAR(80),
  pays VARCHAR(80) DEFAULT 'RDC',
  actif BOOLEAN DEFAULT TRUE,
  cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS entrepots (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(80) NOT NULL UNIQUE,
  localisation VARCHAR(150),
  actif BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS produits (
  id INT AUTO_INCREMENT PRIMARY KEY,
  reference VARCHAR(50) NOT NULL UNIQUE,
  designation VARCHAR(150) NOT NULL,
  description TEXT,
  categorie_id INT NULL,
  fournisseur_id INT NULL,
  unite VARCHAR(20) DEFAULT 'pcs',
  prix_achat DECIMAL(12,2) DEFAULT 0,
  prix_vente DECIMAL(12,2) DEFAULT 0,
  seuil_min INT DEFAULT 0,
  seuil_max INT DEFAULT 0,
  perissable BOOLEAN DEFAULT FALSE,
  date_peremption DATE NULL,
  actif BOOLEAN DEFAULT TRUE,
  cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_prod_cat FOREIGN KEY (categorie_id) REFERENCES categories(id),
  CONSTRAINT fk_prod_four FOREIGN KEY (fournisseur_id) REFERENCES fournisseurs(id),
  INDEX idx_designation (designation)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS stocks (
  produit_id INT NOT NULL,
  entrepot_id INT NOT NULL,
  quantite INT NOT NULL DEFAULT 0,
  maj_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (produit_id, entrepot_id),
  CONSTRAINT fk_stock_prod FOREIGN KEY (produit_id) REFERENCES produits(id) ON DELETE CASCADE,
  CONSTRAINT fk_stock_ent FOREIGN KEY (entrepot_id) REFERENCES entrepots(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS mouvements (
  id INT AUTO_INCREMENT PRIMARY KEY,
  type_mouvement ENUM('ENTREE','SORTIE','TRANSFERT','AJUSTEMENT') NOT NULL,
  produit_id INT NOT NULL,
  quantite INT NOT NULL,
  entrepot_source_id INT NULL,
  entrepot_dest_id INT NULL,
  prix_unitaire DECIMAL(12,2) DEFAULT 0,
  motif VARCHAR(255),
  utilisateur_id INT NOT NULL,
  date_mouvement DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_mvt_prod FOREIGN KEY (produit_id) REFERENCES produits(id),
  CONSTRAINT fk_mvt_user FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id),
  CONSTRAINT fk_mvt_src FOREIGN KEY (entrepot_source_id) REFERENCES entrepots(id),
  CONSTRAINT fk_mvt_dst FOREIGN KEY (entrepot_dest_id) REFERENCES entrepots(id),
  INDEX idx_date (date_mouvement)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS alertes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  type_alerte ENUM('SEUIL_MIN','PEREMPTION','SURSTOCK') NOT NULL,
  produit_id INT NOT NULL,
  message VARCHAR(255),
  niveau ENUM('INFO','WARNING','CRITIQUE') DEFAULT 'WARNING',
  traitee BOOLEAN DEFAULT FALSE,
  cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_alerte_prod FOREIGN KEY (produit_id) REFERENCES produits(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS journal_audit (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  utilisateur_id INT NULL,
  action VARCHAR(50),
  table_cible VARCHAR(50),
  enregistrement_id INT,
  details TEXT,
  horodatage TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_audit_user FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
) ENGINE=InnoDB;

CREATE OR REPLACE VIEW v_stock_global AS
SELECT p.id, p.reference, p.designation, p.unite,
       c.nom AS categorie, f.raison_sociale AS fournisseur,
       p.prix_achat, p.prix_vente, p.seuil_min,
       COALESCE(SUM(s.quantite),0) AS quantite_totale,
       COALESCE(SUM(s.quantite),0) * p.prix_achat AS valeur_stock,
       p.perissable, p.date_peremption, p.actif
FROM produits p
LEFT JOIN stocks s ON s.produit_id = p.id
LEFT JOIN categories c ON c.id = p.categorie_id
LEFT JOIN fournisseurs f ON f.id = p.fournisseur_id
GROUP BY p.id;

CREATE OR REPLACE VIEW v_produits_sous_seuil AS
SELECT * FROM v_stock_global
WHERE quantite_totale <= seuil_min AND actif = TRUE;
