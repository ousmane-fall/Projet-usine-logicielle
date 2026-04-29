# Rapport qualité — TaskFlow

Ce document résume la démarche qualité du projet. L'objectif n'était pas de
cocher le maximum d'outils pour faire bien, mais de mettre en place des
contrôles qui ont du sens et d'être honnête sur ce qui est automatisé, ce qui
est manuel, et ce qu'on n'a pas fait (et pourquoi).

## Les tests

Il y a deux niveaux de tests. Les tests unitaires dans `tests/unit/` testent
chaque fonction isolément : on appelle directement `Calculator.add(2, 3)` et
on vérifie que ça retourne `5`, sans lancer l'app. Les tests d'intégration dans
`tests/integration/` testent l'API de bout en bout : on envoie une vraie requête
HTTP (via le client de test Flask) et on vérifie le code de retour et le JSON.

La couverture de code tourne autour de 96% sur l'ensemble du projet. Le détail
par fichier : `app/__init__.py` est à 84% (les branches d'erreur de démarrage
sont difficiles à tester), `app/api.py` à 97%, `app/calculator.py` à 96%,
`app/models.py` et `app/validators.py` à 100%. Le pipeline CI refuse de passer
si on tombe sous 80%.

Pour lancer les tests localement : `pytest --cov=app --cov-report=term-missing`.

## La qualité du code

On utilise **ruff** pour deux choses : le lint (détecter les imports inutilisés,
les variables non définies, les mauvais patterns) et le formatage (vérifier que
le code est bien mis en forme). Ces deux contrôles sont bloquants en CI : si le
code ne passe pas ruff, le reste du pipeline ne s'exécute pas.

Pour corriger automatiquement le formatage en local : `ruff format app/ tests/`.

On a aussi des outils de qualité supplémentaires disponibles en local mais qui
ne tournent plus en CI : **pylint** pour l'analyse statique avancée, **mypy**
pour la vérification des types, **bandit** pour repérer les patterns dangereux
côté sécurité. Ils restent utiles pendant le développement et sont accessibles
via `./scripts/quality_check.sh`.

## La sécurité

Quelques points concrets. La `SECRET_KEY` de Flask est toujours lue depuis
l'environnement — l'application refuse de démarrer en mode production si elle
n'est pas définie, ce qui évite d'oublier de la configurer sur un serveur.
Le mot de passe Grafana passe aussi par une variable d'environnement, donc
rien n'est jamais en dur dans le code ou dans Git.

La calculatrice mérite une mention particulière : elle n'utilise pas `eval`,
qui exécuterait n'importe quel code Python et serait une faille de sécurité
évidente. À la place, l'expression est parsée avec le module `ast` de Python
et on n'autorise qu'une liste blanche d'opérations (additions, soustractions,
multiplications, divisions). Tout le reste est rejeté.

L'image Docker tourne avec un utilisateur non-root (`appuser`). C'est un réflexe
de base : si le conteneur est compromis, l'attaquant n'a pas les droits root
sur la machine hôte.

## Le pipeline CI/CD

Le pipeline CI se déclenche à chaque push. Il enchaîne trois jobs dans l'ordre :
d'abord la qualité (ruff lint + format), puis les tests (pytest avec le seuil
de couverture), puis le build Docker. Si la qualité échoue, les tests ne
s'exécutent pas. Si les tests échouent, l'image n'est pas construite. Sur les
branches `main` et `dev`, l'image est poussée automatiquement sur GHCR
(le registre Docker de GitHub).

Le pipeline CD est volontairement minimal. Il se déclenche quand la CI passe
sur `main` et fait deux choses : un smoke test Docker (construire l'image,
lancer un conteneur, vérifier que `/api/health` répond) et une validation
Terraform (vérifier que le code d'infra est bien formaté et syntaxiquement
correct). Il ne déploie rien automatiquement sur Azure — c'est un choix assumé
pour éviter de provisionner des ressources payantes à chaque merge.

## La conteneurisation

Le Dockerfile utilise un build multi-stage : une première étape installe les
dépendances Python, une deuxième repart d'une image propre et ne copie que le
résultat. L'image finale est légère car elle ne contient pas pip, les caches
ou les outils de build. L'app tourne avec un utilisateur non-root et un
`HEALTHCHECK` surveille toutes les 30 secondes que l'app répond bien.

## Le monitoring et les logs

L'application expose ses métriques sur `/metrics` via `prometheus_flask_exporter`.
Prometheus les collecte toutes les 10 secondes, Grafana les affiche. Le dashboard
est provisionné automatiquement au premier démarrage, donc pas besoin de le
configurer à la main.

Pour les logs, l'app écrit en JSON sur la sortie standard. Promtail lit ces logs,
les parse et les envoie à Loki. Dans Grafana, on peut ensuite filtrer par niveau
(`level="ERROR"`) ou par module (`logger="app.api"`), ce qui est beaucoup plus
pratique que de grep dans des fichiers texte.

Ce qui manque pour aller plus loin côté observabilité : de l'alerting. Actuellement
on voit ce qui se passe dans Grafana, mais personne n'est notifié si l'app commence
à retourner des erreurs 500. Alertmanager + des règles Prometheus seraient la
suite logique.

## L'infrastructure as code

Terraform décrit l'infrastructure Azure dans des fichiers `.tf` : un Resource
Group, un réseau, un firewall (NSG) avec les ports ouverts pour l'app et le
monitoring, et une petite VM Ubuntu. L'avantage par rapport à cliquer dans
l'interface Azure, c'est que c'est reproductible et versionné dans Git.

Le state Terraform est stocké en local par défaut, ce qui est suffisant pour
une démo individuelle mais qui ne fonctionnerait pas en équipe (deux personnes
ne peuvent pas partager le même state local). En production il faudrait un
backend distant comme Azure Blob Storage.

Ansible prend le relais une fois la VM créée : il se connecte en SSH et installe
Docker, copie le `docker-compose.yml` et lance la stack. Les deux outils se
complètent bien : Terraform gère l'infrastructure, Ansible gère la configuration
logicielle.

## Ce qui pourrait être amélioré

Même logique que dans le README : voici les raccourcis assumés qui mériteraient
d'être comblés pour un contexte de production.

Côté pipeline, le déploiement Azure pourrait être automatisé dans le CD, avec
un backend Terraform distant pour stocker le state. bandit et mypy pourraient
revenir en CI. pip-audit pourrait devenir bloquant avec une politique claire
pour gérer les faux positifs. On pourrait aussi ajouter Trivy pour scanner
les images Docker à la recherche de CVE.

Côté infrastructure, le NSG est actuellement assez ouvert. Les ports de
monitoring (Grafana, Prometheus) devraient être restreints à une IP de confiance
plutôt qu'ouverts au monde. L'app devrait tourner derrière HTTPS avec un
certificat Let's Encrypt. Et SQLite devrait être remplacé par PostgreSQL, avec
des sauvegardes régulières.

Côté organisation, il n'y a qu'un seul environnement. Un projet sérieux aurait
au moins un dev, un staging et une prod, idéalement avec des workspaces Terraform
séparés et des variables d'environnement distinctes.
