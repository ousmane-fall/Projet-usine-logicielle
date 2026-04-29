# TaskFlow

TaskFlow est une petite API de gestion de tâches écrite en Python avec Flask.
Honnêtement, l'application en elle-même n'est pas le vrai sujet du projet :
elle sert surtout de prétexte pour mettre en place une vraie usine logicielle,
avec des tests, du contrôle qualité, du Docker, un pipeline CI/CD, du monitoring,
des logs centralisés et un déploiement infrastructure as code sur Azure.

L'idée était de couvrir toutes les briques classiques d'un projet DevOps,
sans pour autant tomber dans l'over-engineering. Le projet doit rester
compréhensible donc à chaque fois qu'il a fallu
choisir entre "propre mais compliqué" et "simple et clair", on a privilégié
le simple et clair, en notant à la fin du document ce qu'il faudrait améliorer
pour aller en production pour de vrai.

## Démarrer le projet en local

**Tester l'environnement complet (3 commandes) :**

```bash
git clone https://github.com/ousmane-fall/Projet-usine-logicielle.git
cd Projet-usine-logicielle
cp .env.example .env       # editer SECRET_KEY et GRAFANA_ADMIN_PASSWORD
docker compose up -d
```

Au bout d'une vingtaine de secondes, tout tourne :
- API : http://localhost:5000 (test : `curl http://localhost:5000/api/health`)
- Grafana : http://localhost:3000 (admin / mot de passe du `.env`)
- Prometheus : http://localhost:9090

Pour arrêter : `docker compose down` (ajouter `-v` pour effacer aussi les volumes).

### Détails

Le plus simple est d'utiliser Docker Compose, qui va lancer l'application,
Prometheus, Grafana et la stack de logs en une seule commande.

D'abord, on copie le fichier d'exemple des variables d'environnement et on
l'adapte (au minimum la `SECRET_KEY` et le mot de passe Grafana) :

```bash
cp .env.example .env
```

Ensuite on démarre tout :

```bash
docker compose up -d
```

Au bout de quelques secondes, l'application est disponible sur
http://localhost:5000, Grafana sur http://localhost:3000 (compte `admin` avec
le mot de passe défini dans `.env`) et Prometheus sur http://localhost:9090.
Pour vérifier que l'API répond bien, un petit `curl http://localhost:5000/api/health`
suffit. Pour tout arrêter, `docker compose down`, et si on veut aussi effacer
les volumes (base SQLite, dashboards, métriques) on rajoute `-v`.

## L'API

L'API expose une petite gestion de tâches très classique : on peut lister les
tâches, en créer, en modifier, en supprimer, et filtrer par statut. Les routes
disponibles sont `/api/tasks` (GET et POST), `/api/tasks/<id>` (GET, PUT, DELETE),
plus quelques routes utilitaires : `/api/health` pour le healthcheck,
`/api/calculate` qui sait évaluer une expression arithmétique simple, et
`/api/validate` qui valide un email ou un username.

Un exemple pour créer une tâche :

```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Ma premiere tache","status":"todo"}'
```

Et pour la calculatrice :

```bash
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"expression":"1 + 2 * 3"}'
```

Petite précision côté sécurité : la calculatrice n'utilise pas `eval`, qui
serait une porte ouverte à l'injection de code. À la place, l'expression est
parsée avec le module `ast` de Python et on n'autorise qu'une liste blanche
de nœuds (nombres, opérateurs basiques). C'est un bon réflexe à montrer.

## Travailler sur le code

Si on veut développer ou faire tourner les tests sans Docker, il faut juste
installer les dépendances Python (prod et dev) et lancer l'application :

```bash
pip install -r requirements.txt -r requirements-dev.txt
python run.py
```

Pour les tests, c'est `pytest --cov=app --cov-report=term-missing`. La couverture
de code tourne autour de 96%, et la CI refuse de passer en dessous de 80%.

Il y a aussi un script qui fait tourner tous les contrôles qualité d'un coup
(lint, typage, sécurité, tests, complexité) : `./scripts/quality_check.sh`. Avec
l'option `--fast`, il saute les contrôles les plus longs (pip-audit et radon),
ce qui est pratique en développement.

## Le contrôle qualité

Plusieurs outils sont enchaînés pour s'assurer que le code reste propre.
**Ruff** s'occupe du lint et du formatage (c'est l'équivalent moderne et très
rapide de flake8 + black + isort). **Pylint** fait une analyse statique plus
poussée et il faut un score minimum de 7 sur 10 pour passer. **Mypy** vérifie
les annotations de types en mode strict sur le code de l'application.
**Bandit** cherche les patterns dangereux côté sécurité. **Pytest** lance les
tests unitaires et d'intégration, **pytest-cov** mesure la couverture.

Il y a aussi **pip-audit** qui scanne les dépendances pour repérer les CVE
connues, et **radon** qui mesure la complexité cyclomatique. Ces deux derniers
sont gardés en informatif et ne font pas planter la CI : pip-audit parce que
les CVE des dépendances tierces évoluent tous les jours et casseraient le
pipeline pour des raisons indépendantes du code, et radon parce que c'est plus
une métrique d'aide à la lecture qu'un seuil dur à respecter.

## Le pipeline CI/CD

Tout passe par GitHub Actions, avec deux workflows séparés.

Le workflow de **CI** se déclenche à chaque push et chaque pull request. Il
enchaîne quatre jobs : un job qualité qui fait tourner ruff, pylint, mypy,
bandit et pip-audit ; un job test qui lance pytest avec le seuil de couverture ;
un job SonarCloud qui est optionnel et qui ne s'active que si un token a été
configuré (sinon il se contente de skipper sans faire échouer le pipeline,
pour ne pas bloquer ceux qui forkent le projet) ; et enfin un job docker-build
qui construit l'image et la pousse sur GHCR pour les branches `main` et `dev`.

Le workflow de **CD** est volontairement minimal. Il se déclenche après une CI
réussie sur `main` et il fait deux choses : un smoke test Docker (on construit
l'image, on lance le conteneur et on tape sur `/api/health` pour vérifier
qu'elle démarre bien), et une validation Terraform (`fmt` et `validate`).
Il ne fait **pas** de `terraform apply` ni de déploiement Ansible automatique,
et c'est un choix assumé : le but est d'éviter de provisionner par erreur des
ressources Azure payantes à chaque merge sur `main`. Le déploiement réel est
fait à la main quand on en a besoin (voir plus bas).

## Monitoring et logs

L'application expose ses métriques sur `/metrics` grâce à
`prometheus_flask_exporter`. Prometheus est configuré pour les scraper toutes
les 10 secondes, en ajoutant des labels `service=taskflow` et
`environment=production` qui permettent de bien identifier d'où viennent les
métriques.

Grafana est lancé à côté, avec ses datasources Prometheus et Loki déjà
provisionnées et un dashboard TaskFlow disponible dès le premier démarrage.

Pour les logs, l'application les émet directement en JSON, ce qui permet à
Promtail de les parser proprement et de promouvoir des champs comme `level`
ou `logger` en labels Loki. Concrètement, dans Grafana on peut faire des
requêtes du type `{service="taskflow"} | json | level="ERROR"` pour ne voir
que les erreurs, sans avoir à grep dans des fichiers texte.

## Déployer sur Azure (manuel)

Le déploiement Azure se fait en deux temps : d'abord Terraform pour provisionner
l'infrastructure (un Resource Group, un VNet, un NSG et une petite VM Ubuntu),
puis Ansible pour installer Docker dessus et démarrer la stack docker-compose.

Avant de commencer, il faut être connecté à Azure :

```bash
az login
```

Pour la partie Terraform, on se place dans `infra/terraform`, on copie le
fichier d'exemple des variables et on renseigne au moins sa clé SSH publique
ainsi que son IP pour restreindre l'accès aux ports de monitoring :

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

Une fois la VM créée, Terraform affiche son IP publique. On la récupère puis
on passe à Ansible :

```bash
cd ../ansible
# adapter inventory.ini avec l'IP de la VM
ansible-playbook -i inventory.ini playbook.yml \
  --extra-vars "image_tag=latest app_image=ghcr.io/<ton-user>/taskflow"
```

Au bout de quelques minutes, l'application est accessible sur
`http://<ip_de_la_vm>:5000`.

**Très important** une fois la démo terminée : penser à détruire les ressources
pour ne pas continuer à consommer des crédits Azure inutilement.

```bash
cd ../terraform
terraform destroy
```

## Sécurité

Quelques points qui méritent d'être mentionnés. La `SECRET_KEY` de Flask est
toujours lue depuis l'environnement et l'application refuse de démarrer en
production si elle n'est pas définie. Le mot de passe admin de Grafana passe
aussi par une variable d'environnement, donc rien n'est en dur dans le code.
L'image Docker tourne avec un utilisateur non-root (`appuser`), ce qui limite
les dégâts potentiels si jamais le conteneur était compromis. La calculatrice
utilise `ast` plutôt que `eval`, comme expliqué plus haut. Et toutes les entrées
utilisateur (emails, usernames) sont validées avec des regex stricts et des
tailles bornées.

Côté CI, bandit scanne le code à chaque commit, et pip-audit vérifie les
dépendances (en mode informatif).

