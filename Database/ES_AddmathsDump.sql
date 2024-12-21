-- MySQL dump 10.13  Distrib 8.0.40, for Win64 (x86_64)
--
-- Host: localhost    Database: addmaths_es
-- ------------------------------------------------------
-- Server version	8.0.40

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `formulas`
--

DROP TABLE IF EXISTS `formulas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `formulas` (
  `FormulaID` int NOT NULL,
  `FormulaContent` longtext NOT NULL,
  `TopicID` int NOT NULL,
  PRIMARY KEY (`FormulaID`),
  UNIQUE KEY `FormulaID_UNIQUE` (`FormulaID`),
  KEY `Formulas_Topic_FK_idx` (`TopicID`),
  CONSTRAINT `Formulas_Topic_FK` FOREIGN KEY (`TopicID`) REFERENCES `topic` (`TopicID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `formulas`
--

LOCK TABLES `formulas` WRITE;
/*!40000 ALTER TABLE `formulas` DISABLE KEYS */;
/*!40000 ALTER TABLE `formulas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `questions`
--

DROP TABLE IF EXISTS `questions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `questions` (
  `QuestionID` varchar(3) NOT NULL,
  `Description` longtext,
  `TopicID` int NOT NULL,
  PRIMARY KEY (`QuestionID`),
  UNIQUE KEY `QuestionID_UNIQUE` (`QuestionID`),
  KEY `Questions_Topic_FK_idx` (`TopicID`),
  CONSTRAINT `Questions_Topic_FK` FOREIGN KEY (`TopicID`) REFERENCES `topic` (`TopicID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `questions`
--

LOCK TABLES `questions` WRITE;
/*!40000 ALTER TABLE `questions` DISABLE KEYS */;
INSERT INTO `questions` VALUES ('1','Fungsi f diberi sebagai f:x → 5 - 3x.',1),('10a','Diberi bahawa  f:x → x + 1.',1),('10b','Rajah menunjukkan fungsi f yang memetakan set P kepada set Q  dan fungsi g yang memetakan set Q kepada set R.',1),('11','Jadual di bawah menunjukkan harga bagi tiga produk pada tahun 2018 dan 2020 serta indeks harga masing-masing pada tahun 2020 berasaskan tahun 2018.',1),('12','Rajah di bawah menunjukkan sebuah segi tiga PQR  dengan keadaan PQ = 8.5 cm , PR = 7 cm dan &ang;PQR=50&deg;.',1),('2a','Garis lurus y = mx + 1 ialah tangen kepada lengkung x^2 + y^2 - 2x + 4y = 0 . Carikan nilai-nilai m yang mungkin.',2),('2b','Cari julat nilai x jika 7x^2 ≥ 4(5x-3).',2),('3a','Diberi fungsi f(x) = (2x + 5) / 3 dan fg(x) = (2 / x) - 1, x ≠ 0, cari g(3) .',1),('3b','Diberi bahawa fungsi songsang p^(-1)(x) = 4x - 7 .',1),('4a','Tunjukkan bahawa sistem persamaan linear berikut tidak mempunyai penyelesaian. Berikan justifikasi anda. 3x + y - 2z = 0, 2x + 2y - z = -19, 4x - 3z = 8',6),('4b','Garis lurus y - 2x = 3 memotong lengkung 5y - xy = 20  pada dua titik. Hitungkan koordinat titik- titik tersebut.',3),('5','Seorang budak melakukan terjunan dari sebuah pelantar di sebuah kolam renang. Fungsi h(t) = -4t^2 + 8t + 5 dengan keadaan h ialah tinggi, dalam meter dan t ialah masa dalam saat.',2),('6a','Diberi persamaan kuadratik ax^2 + bx + c = 0, dengan keadaan a,b dan c ialah pemalar, a ≠ 0 mempunyai punca-punca α dan β. Tunjukkan bahawa α + β = -b/a  dan αβ =c/a.',2),('6b','Diberi bahawa 3x^2 = px - q mempunyai punca-punca α dan β , dengan keadaan α - 3β = 0. Tunjukkan bahawa p = 4√q.',2),('7','Diberi f(x) = |3x - 5|.',1),('8','Diberi fungsi f(x) = hx^2 - 9x - k, dengan keadaan h dan k ialah pemalar.',2),('9','Diberi f^(-1)(x) = x / 2 dan g(x) = 4x - 3.',5);
/*!40000 ALTER TABLE `questions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `steps`
--

DROP TABLE IF EXISTS `steps`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `steps` (
  `StepID` int NOT NULL,
  `Description` longtext NOT NULL,
  `SubquestionID` varchar(8) DEFAULT NULL,
  `QuestionID` varchar(3) DEFAULT NULL,
  PRIMARY KEY (`StepID`),
  UNIQUE KEY `StepID_UNIQUE` (`StepID`),
  KEY `Steps_Subquestion_FK_idx` (`SubquestionID`),
  KEY `Steps_Question_FK_idx` (`QuestionID`),
  CONSTRAINT `Steps_Question_FK` FOREIGN KEY (`QuestionID`) REFERENCES `questions` (`QuestionID`) ON DELETE CASCADE,
  CONSTRAINT `Steps_Subquestion_FK` FOREIGN KEY (`SubquestionID`) REFERENCES `subquestions` (`SubquestionID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `steps`
--

LOCK TABLES `steps` WRITE;
/*!40000 ALTER TABLE `steps` DISABLE KEYS */;
INSERT INTO `steps` VALUES (1,'\n1. fg(x) = -1 - 3x^2\n2. 5 - 3g(x) = -1 - 3x^2\n3. 6 + 3x^2 = 3g(x)\n4. g(x) = 2 + x^2\n','1a','1'),(2,'\n1. fh(x) = hf(x) = x\n2. Maka h(x) = f^(-1)(x)\n3. Katakan y = 5 - 3x\n4. x = (5-y) / 3\n5. h(x) = (5-x) / 3\n','1b','1'),(3,'\n1. x^2 + (mx + 1)^2 - 2x + 4(mx + 1) = 0 \n2. (1 + m^2)x^2 + (6m - 2)x + 5 = 0\n3. (6m - 2)^2 - 4(1 + m^2)(5) = 0         \n4. 16m^2 - 24m - 16 = 0\n5. m = 2, -1/2\n',NULL,'2a'),(4,'\n1. 7x^2 - 20x + 12 ≥ 0\n2. (7x - 6)(x - 2) ≥ 0     \n3. x ≤ 6/7, x ≥ 2\n',NULL,'2b'),(5,'\n1. (2a+5) / 3 = x\n2. a = (3x-5) / 2\n3. f^(-1)(x) = (3x-5) / 2\n4. g(3) = (3((2/3) - 1)-5) / 2\n5. g(3) = -3\n',NULL,'3a'),(6,'\n1. p(x) = (x+7) / 4\n','3bi','3b'),(7,'\n1. k + 5 = (h+7) / 4\n2. h = 4k + 13\n','3bii','3b'),(8,'\n1. 3x + y - 2z = 0     → (1)\n2. 2x + 2y - z = -19   → (2)\n3. 4x - 3z = 8         → (3)\n4. Hapuskan pemboleh ubah y :  \n5. Persamaan (1) × 2 : 6x + 2y - 4z = 0    → (4)                           \n6. Persamaan (4) - (2) : 4x - 3z = 19      → (5)\n7. Persamaan (5) - (3): 0 = 11\n8. Tetapi 0 ≠ 11\n9. Maka sistem persamaan linear ini tidak mempunyai penyelesaian.\n',NULL,'4a'),(9,'\n1. y - 2x = 3            → (1)\n2. 5y - xy = 20          → (2)\n3. Dari (1): y = 2x + 3  → (3) \n4. Menggantikan (3) ke dalam (2) : 5(2x + 3) - x(2x + 3) = 20   \n5. 2x^2 - 7x + 5 = 0\n6. (x - 1)(2x - 5) = 0                                                     \n7. x = 1, x = 5/2\n8. Apabila x = 1, y = 5\n9. Apabila x = 5/2, y = 8\n10. Maka titik persilangan ialah : (1,5) dan (5/2,8).\n',NULL,'4b'),(10,'\n1. h(0) = 5\n','5a','5'),(11,'\n1. x = -8 / (2(-4))\n2. x = 1\n','5b','5'),(12,'\n1. h(1) =-4(1)^2 + 8(1) + 5\n2. h = 9\n','5c','5'),(13,'\n1. h(t) = 0\n2. -4t^2 + 8t + 5 = 0\n3. (2t - 5)(2t + 1) = 0\n4. t = 5/2, -1/2\n5. 0 ≤ t ≤ 5/2\n','5d','5'),(14,'\n1. x^2 + (b/a)x +  c/a = 0   → (1)\n2. (x - α)(x - β) = 0 \n3. x^2 - (α + β)x + αβ = 0   → (2)\n4. Bandingkan (1) dan (2) , α + β = -b/a  dan αβ = c/a\n',NULL,'6a'),(15,'\n1. α + β = 4β = p/3    → (1)\n2. αβ = 3β^2 = q/3     → (2)\n3. β = p/12            → (3)\n4. Gantikan (3) ke dalam (2)\n5. 3(p/12)^2 = q/3\n6. p^2 = (144/9)q\n7. p = 4√q\n',NULL,'6b'),(16,'\n1. f(x) ialah fungsi.\n2. f(x) adalah hubungan banyak kepada satu.Setiap objek dalam domain mempunyai hanya satu imej dalam kodomain.\n','7a','7'),(17,'\n1. Jawapan dalam graf.\n','7b','7'),(18,'\n1. |3x - 5| = x \n2. 3x - 5 = x\n3. 2x = 5\n4. x = 5/2\n5. 3x - 5 = -x\n6. 4x = 5\n7. x = 5/4\n','7c','7'),(19,'\n1. f(x) = h(x^2 - (9/h)x) - k\n2.	    = h[x^2 - (9/h)x + (-9/2h)^2 - (-9/2h)^2] - k\n3.      = h(x - 9/2h)^2 - h(81/(4h^2)) - k\n4.      = h(x - 9/2h)^2 - 81/4h - k\n5.      = h(x - 9/2h)^2 - ((81 + 4kh))/4h\n','8a','8'),(20,'\n1. 9/2h = 9/4\n2. h = 2\n3. -121/8 = -((81 + 4kh))/4h\n4. -121/8 = -[81 + 4k(2)]/(4(2))\n5. k=5\n6. 2x^2 - 9x - 5 = 0\n7. (x - 5)(2x + 1) = 0\n8. x = 5, x = -1/2\n','8b','8'),(21,'\n1. x = (f(x))/2\n2. f(x) = 2x\n','9a','9'),(22,'\n1. f^2(x) = 2(2x)\n2.        = 4x\n','9bi','9'),(23,'\n1. f^2(x) = 2(2x) = 4x = 2x * 2^1\n2. f^3(x) = 4(2x) = 8x = 2x * 2^2\n3. f^4(x) = 8(2x) = 16x = 2x * 2^3\n4. f^n(x) = 2x * 2^(n-1)\n','9bii','9'),(24,'\n1. g^(-1)(x) = (x + 3)/4\n2. f^(-1)g^(-1)(x) = (((x + 3)/4))/2\n3.                 = (x + 3)/8\n4. (gf)(x) = 4(2x) - 3\n5.         = 8x - 3\n6. (gf)^(-1)(x) = (x + 3)/8\n7.∴ f^(-1)g^(-1)(x) = (gf)^(-1)(x) is proven\n','9c','9'),(25,'\n1. f^2(x) = (x + 1) + 1 = x + 2\n','10ai','10a'),(26,'\n1. f^3(x) = ff^2(x) = (x +  2) + 1 = x + 3\n','10aii','10a'),(27,'\n1. f^4(x) = ff^3(x) = (x + 3) + 1 = x + 4\n','10aiii','10a'),(28,'\n1. Secara am, f^n(x) = x + n\n2. Maka f^50(x) = x + 50\n','10aiv','10a'),(29,'\n1. f(m) = 5, (m + 1)/2 = 5\n2. m = 9           \n3. g^(-1)(n) = 5, (n + 20)/4 = 5\n4. n = 0  \n','10bi','10b'),(30,'\n1. g^(-1)(x) = (x + 20)/4\n2. Katakan y = (x + 20)/4\n3. Maka g(x) = 4x - 20\n4. Fungsi yang memetakan set P ke set R:\n5. gf(x) = g((x + 1)/2) = 4((x + 1)/2) - 20\n6.       = 2x - 18\n','10bii','10b'),(31,'\n1. a = 72/45 × 100, a = 160\n2. b/50 × 100 = 180, b = 90\n','11a','11'),(32,'\n1. ((160 * 300) + (180 * 700) + 145c)/(300 + 700 + c) = 170\n2. c = 160\n','11b','11'),(33,'\n1. P_2020/6600 * 100 = 170\n2. P_2020 = RM 11220\n','11c','11'),(34,'\n1. (170 * I_(2022/2020))/100 = 190\n2. I_(2022/2020) = 111.76 \n3. Peratus kenaikan dari tahun 2020 ke tahun 2022 ialah 11.76%\n','11d','11'),(35,'\n1. sin R/8.5 = sin 50&deg;/7\n2. Sudut cakah PRQ = 180&deg; - 68.47&deg;\n3.                 = 111.53&deg;\n','12ai','12'),(36,'\n1. &ang; P = 180&deg; - 111.53&deg; - 50&deg;  \n2.         = 18.47&deg;\n3. Luas segi tiga PQR = 1/2(8.5)(7) sin 18.47&deg;\n4.                    = 9.425cm^2\n','12aii','12'),(37,'\n1. Jawapan dalam graf.\n','12b','12'),(38,'\n1. Menggunakan Segi tiga bersudut tegak\n2. sin 50&deg; = PR/8.5\n3. PR = 6.511 cm\n','12c','12');
/*!40000 ALTER TABLE `steps` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `subquestions`
--

DROP TABLE IF EXISTS `subquestions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `subquestions` (
  `SubquestionID` varchar(8) NOT NULL,
  `Description` longtext NOT NULL,
  `QuestionID` varchar(3) NOT NULL,
  PRIMARY KEY (`SubquestionID`),
  KEY `Subquestions_Question_FK_idx` (`QuestionID`),
  CONSTRAINT `Subquestions_Question_FK` FOREIGN KEY (`QuestionID`) REFERENCES `questions` (`QuestionID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `subquestions`
--

LOCK TABLES `subquestions` WRITE;
/*!40000 ALTER TABLE `subquestions` DISABLE KEYS */;
INSERT INTO `subquestions` VALUES ('10ai','Cari f^2(x),','10a'),('10aii','Cari f^3(x),','10a'),('10aiii','Cari f^4(x),','10a'),('10aiv','Cari f^50(x).','10a'),('10bi','Cari nilai m dan nilai n,','10b'),('10bii','Cari fungsi yang memetakan set P kepada set R.','10b'),('11a','Cari nilai a dan b.','11'),('11b','Jika nilai indeks gubahan bagi harga produk-produk tersebut pada tahun 2020 berasaskan tahun 2018 ialah 170, cari nilai c.','11'),('11c','Diberi bahawa perbelanjaan bagi pembelian produk-produk itu itu pada tahun 2018 ialah RM6600, hitungkan perbelanjaan yang sepadan untuk tahun 2020.','11'),('11d','Diberi bahawa nilai indeks gubahan bagi harga produk-produk tersebut pada tahun 2022 berasaskan tahun 2018 ialah 190. Hitung peratus kenaikan harga produk-produk itu dari tahun 2020 ke tahun 2022.','11'),('12ai','Hitungkan sudut cakah PRQ,','12'),('12aii','Hitungkan luas segi tiga PQR.','12'),('12b','Lakarkan dan labelkan sebuah segi tiga yang berlainan daripada segi tiga PQR dengan keadaan ukuran panjang PQ dan PR serta sudut PQR dikekalkan.','12'),('12c','Jika panjang PR dikurangkan manakala panjang PQ dan sudut PQR dikekalkan, hitung panjang PR supaya hanya satu segi tiga PQR dapat dibina.','12'),('1a','Jika g ialah satu fungsi lain dengan keadaan fg:x → -1 - 3x^2, tentukan fungsi g','1'),('1b','Diberi bahawa fh(x) = hf(x) = x,tentukan fungsi h','1'),('3bi','Cari p(x),','3b'),('3bii','Seterusnya, ungkapkan h dalam sebutan k jika p^(-1) p(k + 5) = p(h).','3b'),('5a','Cari tinggi pelantar dari permukaan air, dalam meter,','5'),('5b','Cari masa yang dicapai oleh budak itu pada ketinggian maksimumnya, dalam saat,','5'),('5c','Cari tinggi maksimum yang dicapai oleh budak itu, dalam meter,','5'),('5d','Cari julat masa selama budak itu berada di udara, dalam saat.','5'),('7a','Tentukan samada f(x) adalah satu fungsi atau tidak.','7'),('7b','Lakarkan f(x)=|3x - 5| untuk -1 ≤ x ≤ 5.','7'),('7c','Cari nilai-nilai x jika f(x) = x.','7'),('8a','Tunjukkan bahawa f(x) = h(x - 9/2h)^2 - ((81 + 4kh))/4h','8'),('8b','Jika titik minimum bagi f(x) ialah (9/4,-121/8), cari nilai bagi h dan k. Seterusnya, selesaikan persamaan kuadratik f(x) = 0 .','8'),('9a','Cari f(x).','9'),('9bi','Cari f^2(x),','9'),('9bii','Cari fungsi f^n(x) dalam sebutan n dan x.','9'),('9c','Tunjukkan bahawa f^(-1) g^(-1) (x)=(gf)^(-1) (x).','9');
/*!40000 ALTER TABLE `subquestions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `topic`
--

DROP TABLE IF EXISTS `topic`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `topic` (
  `TopicID` int NOT NULL,
  `TopicName` varchar(45) NOT NULL,
  PRIMARY KEY (`TopicID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `topic`
--

LOCK TABLES `topic` WRITE;
/*!40000 ALTER TABLE `topic` DISABLE KEYS */;
INSERT INTO `topic` VALUES (1,'Fungsi'),(2,'Fungsi Kuadratik'),(3,'Sistem Persamaan'),(4,'Indeks, Surd, dan Logaritma'),(5,'Janjang'),(6,'Hukum Linear'),(7,'Geometri Koordinat'),(8,'Vektor'),(9,'Penyelesaian Segi Tiga'),(10,'Nombor Indeks');
/*!40000 ALTER TABLE `topic` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-12-16 20:25:13
