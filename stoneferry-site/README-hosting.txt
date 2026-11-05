STONEFERRY TRADING - website files

index.html            the whole site (one page; CSS and JS are inside it)
favicon.ico/.svg      browser tab icons
apple-touch-icon.png  iPhone home-screen icon
og-image.png          preview image when the link is shared (LinkedIn, WhatsApp, iMessage)

HOW TO PUT IT ON stoneferrytrading.com (about 15 minutes, free)

1. Go to app.netlify.com and create a free account (sign in with GitHub or email).
2. On the Sites page, drag this whole folder onto the "drag and drop your site" box.
   Netlify gives you a temporary address like random-name.netlify.app. Open it and check the site.
3. In Netlify: Site configuration > Domain management > Add a domain > stoneferrytrading.com.
   Netlify shows you the DNS records it needs.
4. In GoDaddy > My Products > stoneferrytrading.com > DNS:
   - edit the A record for "@" and set it to the IP address Netlify shows
   - edit the CNAME record for "www" and point it to your random-name.netlify.app
   Leave the MX, TXT and other records alone (they run your email).
5. Wait 10-60 minutes. Netlify issues the HTTPS certificate automatically.

PHOTOS
The five photos are loaded from Unsplash (free license, no attribution required). To stop depending on Unsplash, download each photo from the links below,
put the files in this folder, and change the image URLs in index.html:
- hero:     https://unsplash.com/photos/rows-of-green-crops-in-field-at-sunset-IQVFVH0ajag
- products: https://unsplash.com/photos/flat-lay-photography-of-spices-on-plate-i0IvwAhhGZM
- process:  https://unsplash.com/photos/a-field-of-plants-W48i6oMFSCM
- process:  https://unsplash.com/photos/container-ship-at-industrial-port-yx20mpDyr2I
- company:  https://unsplash.com/photos/2tTjRZ0PRFM
Replace them with your own photos from the Egypt visit as soon as you have them.

THE SAMPLE-REQUEST FORM
It composes an email to omar@stoneferrytrading.com (opens the visitor's email app, with a copy button
as backup). No server needed. If you want submissions delivered without the email step, Netlify Forms
can do it: add  data-netlify="true"  to the <form> tag and remove the preventDefault line in the script.

EDITING TEXT
Open index.html in any editor. Each section is marked with <section id="...">.
