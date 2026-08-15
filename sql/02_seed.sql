USE gestion_stock;

INSERT IGNORE INTO roles (nom, description) VALUES
 ('admin','Acces total au systeme'),
 ('gestionnaire','Gestion produits, fournisseurs et mouvements'),
 ('vendeur','Consultation et sorties de stock');

INSERT IGNORE INTO entrepots (nom, localisation) VALUES
 ('Depot Central','Kinshasa - Gombe'),
 ('Depot Secondaire','Kinshasa - Limete'),
 ('Boutique','Kinshasa - Matonge');

INSERT IGNORE INTO categories (nom, description) VALUES
 ('Informatique','Materiel et accessoires informatiques'),
 ('Bureautique','Fournitures de bureau'),
 ('Alimentaire','Produits alimentaires perissables'),
 ('Hygiene','Produits d entretien et hygiene'),
 ('Electromenager','Appareils electromenagers');

INSERT IGNORE INTO fournisseurs (raison_sociale, contact, telephone, email, ville) VALUES
 ('TechnoPlus SARL','Jean Kabila','+243810000001','contact@technoplus.cd','Kinshasa'),
 ('BureauPro','Marie Ilunga','+243810000002','info@bureaupro.cd','Kinshasa'),
 ('AgroDistrib','Paul Mbala','+243810000003','vente@agrodistrib.cd','Lubumbashi'),
 ('CleanHouse','Sarah Nzuzi','+243810000004','sarah@cleanhouse.cd','Kinshasa');
