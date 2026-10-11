# Security policy

fundtrail is an early prototype and has had no security audit.

## Reporting a vulnerability in fundtrail

Please do not open a public issue for a security problem in the tool itself.
Use GitHub's private vulnerability reporting on this repository
("Security" tab, "Report a vulnerability"). We aim to reply within 7 days.

## Scope

In scope: bugs in fundtrail's code, for example unsafe parsing of RPC or feed
responses, or wrong labels that could mislead an incident responder.

Out of scope: vulnerabilities in the protocols, chains or RPC providers that
fundtrail observes. Report those to the affected project or its bug bounty.

## Using the output

Trace output is a lead, not proof. Check findings on a block explorer before
acting on them, and treat any address label as a claim to be verified.
