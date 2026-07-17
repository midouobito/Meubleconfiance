-- ============================================================
-- storage_policy.sql
-- Exécutez ce script dans l'éditeur SQL de Supabase
-- pour permettre à l'administrateur d'ajouter des images.
-- ============================================================

-- Autoriser l'administrateur connecté à ajouter des images
CREATE POLICY "Admin can upload images"
ON storage.objects FOR INSERT TO authenticated WITH CHECK ( bucket_id = 'facebook-media' );

-- Autoriser l'administrateur connecté à modifier/supprimer des images
CREATE POLICY "Admin can update images"
ON storage.objects FOR UPDATE TO authenticated USING ( bucket_id = 'facebook-media' );

CREATE POLICY "Admin can delete images"
ON storage.objects FOR DELETE TO authenticated USING ( bucket_id = 'facebook-media' );
