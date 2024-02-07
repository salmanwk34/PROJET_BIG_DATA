from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import StringType, DoubleType, IntegerType

# Initialisation de la session Spark
spark = SparkSession.builder \
    .appName("ETL OpenFoodFacts") \
    .config("spark.mongodb.input.uri", "mongodb://mongodb:27017/dump.products") \
    .config("spark.mongodb.output.uri", "mongodb://mongodb:27017/dump.products") \
    .config("spark.jars", "/opt/application/postgresql-42.7.1.jar") \
    .getOrCreate()

# Lecture des données depuis MongoDB
df_products = spark.read.format("mongo").load()

# Chargement des données des régimes et des utilisateurs (stockées localement)
df_regimes = spark.read.csv("/opt/application/regimes.csv", header=True, inferSchema=True)
df_utilisateurs = spark.read.csv("/opt/application/utilisateurs.csv", header=True, inferSchema=True)

# Nettoyage et transformation des données
df_products_filtered = df_products.filter(
    df_products["product_name"].isNotNull() & 
    df_products["countries"].isNotNull() & 
    df_products["nutriments.energy_100g"].isNotNull()
)

# Convertir les colonnes nécessaires aux types appropriés
df_final = df_products_filtered.withColumn("energy_100g", col("nutriments.energy_100g").cast(DoubleType()))

# Préparer les autres colonnes ici si nécessaire

# Joindre les DataFrames
df_final = df_final.join(df_utilisateurs, df_final["product_name"] == df_utilisateurs["regime_suivi"])

# Écriture des résultats dans PostgreSQL
df_final.write \
    .format("jdbc") \
    .option("url", "jdbc:postgresql://postgres:5432/EPSI") \
    .option("dbtable", "menus") \
    .option("user", "salman") \
    .option("password", "masterepsi99") \
    .option("driver", "org.postgresql.Driver") \
    .mode("overwrite") \
    .save()

# Fermeture de la session Spark
spark.stop()
