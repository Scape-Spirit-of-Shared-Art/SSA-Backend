/*
  Warnings:

  - Added the required column `categories` to the `places` table without a default value. This is not possible if the table is not empty.

*/
-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_places" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "bio" TEXT NOT NULL,
    "website" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "phone_number" TEXT NOT NULL,
    "address" TEXT NOT NULL,
    "floormaps" TEXT NOT NULL,
    "categories" TEXT NOT NULL,
    "password" TEXT NOT NULL,
    "monday_friday" TEXT NOT NULL,
    "saturday" TEXT NOT NULL,
    "sunday" TEXT NOT NULL,
    "image_path" TEXT NOT NULL,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME NOT NULL
);
INSERT INTO "new_places" ("address", "bio", "created_at", "email", "floormaps", "id", "image_path", "monday_friday", "name", "password", "phone_number", "saturday", "sunday", "updated_at", "website") SELECT "address", "bio", "created_at", "email", "floormaps", "id", "image_path", "monday_friday", "name", "password", "phone_number", "saturday", "sunday", "updated_at", "website" FROM "places";
DROP TABLE "places";
ALTER TABLE "new_places" RENAME TO "places";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
